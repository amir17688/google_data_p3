"""A simple plugin manager. Rolling my own for three reasons:
   1) Environmental scan did not give me quite what I wanted.
   2) The super simple examples didn't support automatic/dynamic loading.
   3) I kinda wanted to understand the process :)
"""

import os, sys
from datetime import datetime
import dir_watcher
import inspect
from IPython.utils.coloransi import TermColors as color
#pylint: disable=no-member

class PluginManager(object):
    """Plugin Manager for Workbench."""

    def __init__(self, plugin_callback, plugin_dir = 'workers'):
        """Initialize the Plugin Manager for Workbench.

        Args:
            plugin_callback: The callback for plugin. This is called when plugin is added.
            plugin_dir: The dir where plugin resides.
        """

        # Set the callback, the plugin directory and load the plugins
        self.plugin_callback = plugin_callback
        self.plugin_dir = plugin_dir
        self.load_all_plugins()

        # Now setup dynamic monitoring of the plugins directory
        self.watcher = dir_watcher.DirWatcher(self.plugin_path)
        self.watcher.register_callbacks(self.on_created, self.on_modified, self.on_deleted)
        self.watcher.start_monitoring()

    def load_all_plugins(self):
        """Load all the plugins in the plugin directory"""

        # Go through the existing python files in the plugin directory
        self.plugin_path = os.path.realpath(self.plugin_dir)
        sys.path.append(self.plugin_dir)
        print '<<< Plugin Manager >>>'
        for f in [os.path.join(self.plugin_dir, child) for child in os.listdir(self.plugin_dir)]:

            # Skip certain files
            if '.DS_Store' in f or '__init__.py' in f: 
                continue

            # Add the plugin
            self.add_plugin(f)

    def on_created(self, file_list):
        """Watcher callback

        Args:
            event: The creation event.
        """
        for plugin in file_list:
            self.add_plugin(plugin)

    def on_modified(self, file_list):
        """Watcher callback.

        Args:
            event: The modification event.
        """
        for plugin in file_list:
            self.add_plugin(plugin)

    def on_deleted(self, file_list):
        """Watcher callback.

        Args:
            event: The modification event.
        """
        for plugin in file_list:
            self.remove_plugin(plugin)

    def remove_plugin(self, f):
        """Remvoing a deleted plugin.

        Args:
            f: the filepath for the plugin.
        """
        if f.endswith('.py'):
            plugin_name = os.path.splitext(os.path.basename(f))[0]
            print '- %s %sREMOVED' % (plugin_name, color.Red)
            print '\t%sNote: still in memory, restart Workbench to remove...%s' % \
                  (color.Yellow, color.Normal)

    def add_plugin(self, f):
        """Adding and verifying plugin.

        Args:
            f: the filepath for the plugin.
        """
        if f.endswith('.py'):

            # Just the basename without extension
            plugin_name = os.path.splitext(os.path.basename(f))[0]

            # It's possible the plugin has been modified and needs to be reloaded
            if plugin_name in sys.modules:
                try:
                    handler = reload(sys.modules[plugin_name])
                    print'\t- %s %sRELOAD%s' % (plugin_name, color.Yellow, color.Normal)
                except ImportError, error:
                    print 'Failed to import plugin: %s (%s)' % (plugin_name, error)
                    return
            else:
                # Not already loaded so try to import it
                try:
                    handler = __import__(plugin_name, globals(), locals(), [], -1)
                except ImportError, error:
                    print 'Failed to import plugin: %s (%s)' % (plugin_name, error)
                    return

            # Run the handler through plugin validation
            plugin = self.validate(handler)
            print '\t- %s %sOK%s' % (plugin_name, color.Green, color.Normal)
            if plugin:

                # Okay must be successfully loaded so capture the plugin meta-data,
                # modification time and register the plugin through the callback
                plugin['name'] = plugin_name
                plugin['dependencies'] = plugin['class'].dependencies
                plugin['docstring'] = plugin['class'].__doc__
                plugin['mod_time'] = datetime.utcfromtimestamp(os.path.getmtime(f))

                # Plugin may accept sample_sets as input
                try:
                    plugin['sample_set_input'] = getattr(plugin['class'], 'sample_set_input')
                except AttributeError:
                    plugin['sample_set_input'] = False

                # Now pass the plugin back to workbench
                self.plugin_callback(plugin)

    def validate(self, handler):
        """Validate the plugin, each plugin must have the following:
            1) The worker class must have an execute method: execute(self, input_data).
            2) The worker class must have a dependencies list (even if it's empty).
            3) The file must have a top level test() method.

        Args:
            handler: the loaded plugin.
        """

        # Check for the test method first
        test_method = self.plugin_test_validation(handler)
        if not test_method:
            return None

        # Here we iterate through the classes found in the module and pick
        # the first one that satisfies the validation
        for name, plugin_class in inspect.getmembers(handler, inspect.isclass):
            if self.plugin_class_validation(plugin_class):
                return {'class':plugin_class, 'test':test_method}

        # If we're here the plugin didn't pass validation
        print 'Failure for plugin: %s' % (handler.__name__)
        print 'Validation Error: Worker class is required to have a dependencies list and an execute method'
        return None

    def plugin_test_validation(self, handler):
        """Plugin validation.
        
        Every workbench plugin must have top level test method.

        Args:
            handler: The loaded plugin.

        Returns:
            None if the test fails or the test function.
        """
        methods = {name:func for name, func in inspect.getmembers(handler, callable)}
        if 'test' not in methods.keys():
            print 'Failure for plugin: %s' % (handler.__name__)
            print 'Validation Error: The file must have a top level test() method'
            return None
        else:
            return methods['test']

    def plugin_class_validation(self, plugin_class):
        """Plugin validation 
        
        Every workbench plugin must have a dependencies list (even if it's empty). 
        Every workbench plugin must have an execute method.

        Args:
            plugin_class: The loaded plugun class.

        Returns:
            True if dependencies and execute are present, else False.
        """

        try:
            getattr(plugin_class, 'dependencies')
            getattr(plugin_class, 'execute')
        except AttributeError:
            return False

        return True


# Just create the class and run it for a test
def test():
    """Executes plugin_manager.py test."""

    # This test actually does more than it appears. The workers directory
    # will get scanned and stuff will get loaded into workbench.
    def new_plugin(plugin):
        """new plugin callback """
        print '%s' % (plugin['name'])

    # Create Plugin Manager
    plugin_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)),'../workers')
    PluginManager(new_plugin, plugin_dir=plugin_dir)

if __name__ == "__main__":
    test()

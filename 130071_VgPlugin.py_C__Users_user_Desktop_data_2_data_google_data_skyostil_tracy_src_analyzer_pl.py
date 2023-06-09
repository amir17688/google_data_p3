# Copyright (c) 2011 Nokia
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import Plugin
import VgReport
import VgTraceOperations

class VgPlugin(Plugin.InteractivePlugin):
  def __init__(self, analyzer):
    self.analyzer = analyzer
    self.analyzer.registerCommand("report",         self.generateTraceReport)

  def generateTraceReport(self, traceName, path = None, format = "html"):
    """
    Generate a performance report of a trace.
    """
    if not traceName in self.analyzer.traces:
      self.analyzer.fail("Trace not found: %s" % traceName)
      
    trace         = self.analyzer.traces[traceName]
    traceFileName = self.analyzer.traceFiles.get(traceName, None)
    
    if not path:
      path = traceFileName.split(".", 1)[0] + "_report"
    
    VgReport.generateReport(self.analyzer.project, trace, traceFileName, path, format)
    self.analyzer.reportInfo("Performance report saved to '%s'." % (path))

  def postProcessInstrumentationData(self, trace):
    VgTraceOperations.calculateStatistics(self.analyzer.project, trace)

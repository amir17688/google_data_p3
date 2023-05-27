# 1 = only crash errors
# 2 = error + warning
# 3 = All output
error_level = 3


#functions available : Onclose, Onopen
auto_function_macro = "onOpen"
trigger_close_test_value="True"
trigger_close_test_name = "toto"

#methods available: variables
key_hiding_method = "doc_variable"

#encroyption available : xor
encryption_type = "xor"
encryption_key_length = 50000 #Max is 65280 for Document.Variable method

#Regex
variable_name_ex = "toto"
regex_rand_var = '\[rdm::([0-9]+)\](\w*)' #regex that select the name of the variable, after the delimiter and the length
regex_rand_del = '\[rdm::[0-9]+\]' #regex should select only the delimiter

regex_defaut_string = '[\'\"](.+?)[\'\"]' #Regex that select all string except the one follow by exception string
regex_exclude_string_del = '\[!!\]' #The exclusion is to avoid vba string that could finish with exclude characters.
exclude_mark = '[!!]'

regex_string_to_hide = '\[var::(\w*)\]'
regex_string_to_hide_find = '\[var::'+variable_name_ex+'\]'

#Office informations
template_file = r"C:\tmp\Vbad\Example\Template\template.doc"
filename_list = r"C:\tmp\Vbad\Example\Lists\filename_list.txt"

#saving informations
path_gen_files = r"C:\tmp\Vbad\Example\Results"

#Malicious VBS Information:
#All data you want to encrypt and include in your doc
original_vba_file = r"C:\tmp\Vbad\Example\Orignal_VBA\original_vba_prepared.vbs"
trigger_function_name =  "Test" #Function that you want to auto_trigger (in your original_vba_file)
string_to_hide = {"domain_name":"http://www.test.com", "path_to_save":r"C:\tmp\toto"}

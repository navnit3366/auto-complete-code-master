import re
import os
from os.path import join
import DB

database = DB.DATABASE()

class ClassParser(object):
   class_expr = re.compile(r'class (.+?)(?:\((.+)*\))?\:')
   python_file_expr = re.compile(r'(.+?\.py)')
   methodre = re.compile(r'def (.+?)(?:\((.*?)\))?\s*:')
   variable = re.compile(r'\s*(.+?)\s*=\s*(.+)')
   objectre = re.compile(r'\s*(.+?)\s*=\s*(.+)\.(.+)')

   indent = "    "
   def findAllClasses(self, python_file):
      #Read in a python file and return all the class names
      with open(python_file) as infile:
         everything = infile.read()
         class_names = ClassParser.class_expr.findall(everything)
         return class_names

   def findAllPythonFiles(self, directory):
      #Find all the python files starting from a top level directory

      python_files = []
      for root, dirs, files in os.walk(directory):
         for file in files:
            if ClassParser.python_file_expr.match(file):
               python_files.append(join(root,file))
      return python_files

   def parse(self, file):
      """ Parse the directory and spit out a csv file
      """
      try:
        dbDictinoary=database.selectIncrementedCount()
        if self.getTail(file).replace('.py','') in database.getAll_modules():
            database.truncateModule(self.getTail(file))
        classes = self.findAllClasses(file)
        self.addNameeModule(file)
        self.addNameeClasses(file, classes)  #Name of classes of every file
        self.method_modules(file)
        self.variable_moudles(file)
        for classname in classes:
            self.findClassemethod(classname[0],file)
            self.findClassevariables(classname[0],file)
        database.updateCount(dbDictinoary)
        database.conn.commit()
      except:
          print('cant open file')
   def findClassemethod(self, classname , python_file):
       #Read in a python file and return all the class methodes

       classnamere = re.compile(r'class '+classname+'(?:\((.+)*\))?\:')
       methods = []
       with open(python_file) as infile:
            flag = True
            for line in infile.readlines():
                if flag == False:
                    if self.indent in line and line.count(self.indent)==1:
                        methods += self.methodre.findall(line)
                    elif not self.indent in line and line[0].isalpha():
                        break
                if flag == True:
                    class_name = classnamere.findall(line)
                    if class_name:
                        flag = False
       #print( python_file ,' ',classname , ' : ' ,methods)
       self.addmethodClass(python_file,classname,methods)

   def findClassevariables(self, classname, python_file):
       varibles = []
       classnamere = re.compile(r'class ' + classname + '(?:\((.+)*\))?\:')
       with open(python_file) as infile:
           flag = True
           for line in infile:
               if flag == False:
                   if self.indent in line and line.count(self.indent)==1:
                       if not 'def' in line and not 'class' in line:
                           if '.' in line:
                            varibles += self.objectre.findall(line)
                           else:
                               varibles += self.variable.findall(line)
                   elif not self.indent in line and line[0].isalpha():
                       break
               if flag == True:
                   class_name = classnamere.findall(line)
                   if class_name:
                       flag = False
       #print(classname, ' : ', varibles)
       self.addvariableClass(python_file,classname,varibles)

   def method_modules(self,python_file):
        methods = []
        with open(python_file) as infile:
           for line in infile:
               if not self.indent in line:
                   methods += self.methodre.findall(line)
        #print(python_file ,' method for modules' , methods)
        self.addmethodModule(python_file,methods)

   def variable_moudles(self, python_file):
       varibles = []
       with open(python_file) as infile:
           for line in infile:
               if not self.indent in line and not 'def' in line and not 'class' in line:
                   if '.' in line:
                       varibles += self.objectre.findall(line)
                   else:
                       varibles += self.variable.findall(line)
       #print('varibles for modules', varibles)
       self.addvariableModule(python_file,varibles)


   def getTail(self,python_file):
       head, tail = os.path.split(python_file)
       return tail

   def addNameeModule(self,modulename):
        tail = self.getTail(modulename)
        database.addModule(tail)                       #should be enabled if new module is made because there is unique constraints in moduleName column

   def addNameeClasses(self,python_file,classnameS):
       tail = self.getTail(python_file)

       for classname in classnameS:
           database.addClass(tail,classname[0],classname[1])


   def addmethodModule(self, python_file,methods):
       tail = self.getTail(python_file)
       for method in methods:
          database.addModuleMethods(tail , method[0])
        #print ('module:', tail,'function: ',method[0],'parameter:',method[1])


   def getClassesNameas(self,python_file):
       module_class = []
       classes = self.findAllClasses(python_file)
       for classname in classes:
           module_class.append(classname[0])
       return module_class

   def addvariableModule(self, python_file,varibles):
       tail = self.getTail(python_file)
       module_class=self.getClassesNameas(python_file)
       #print ("calsses : --> ",module_class)
       for variable in varibles:
           if(len(variable)>2):
               database.addModuleVariables(tail,variable[0],variable[2],variable[1],2)
              # print ('module:', tail,
               # 'object:',variable[0],'moduleOfobject:',variable[1],'class:',variable[2])
           else:
                if variable[1] in module_class :#can check if object in classnames or Not if found then 'object:'=variable[0]& 'class:',variable[1]
                    #print('module:', tail, 'object:', variable[0], 'Class:', variable[1])
                    database.addModuleVariables(tail,variable[0],variable[1],None,1) #add object
                else:
                    #print('module:', tail, 'object:', variable[0], 'Value:', variable[1])
                     database.addModuleVariables(tail, variable[0], None,None, 0) #add Normal variable


   def addvariableClass(self,python_file,classname,varibles):
       tail = self.getTail(python_file)
       module_class=self.getClassesNameas(python_file)
       for variable in varibles:
           if (len(variable) > 2):
                database.addClass_object_othermodule(classname,variable[0],variable[2],variable[1])
                #print ('module:', tail,'className:',classname, 'object:', variable[0], 'moduleOfobject:', variable[1], 'class:', variable[2])
           else:
               if variable[1] in module_class: #3mlt object mn nfs el module y3ne el classen mojdeen fe nfs el module
                   database. addClass_object_variable(classname,variable[0],variable[1])
                   #print ('module:', tail,'className:',classname, 'object:', variable[0], 'Class:', variable[1])
               else: #VARIABLE 3ADY
                   database.addClass_Normalvariable(classname,variable[0])
                   #print ('module:', tail,'className:',classname, 'object:', variable[0], 'Value:', variable[1])

   def addmethodClass(self, python_file,classname,methods):
       tail = self.getTail(python_file)
       for method in methods:
           database.addfunctionsinclass(classname,method[0])
           #print ('module:', tail, 'className:',classname, 'function:', method[0], 'parameter:', method[1])


# if __name__=="__main__":
#    parser = ClassParser()
#    dir_path = os.path.dirname(os.path.realpath(__file__)) + os.sep +"code-files"
#    parser.parse(dir_path)
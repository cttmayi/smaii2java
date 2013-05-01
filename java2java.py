#import re
import os
import sys

class smali2java():
    
    def __init__(self):
        self.className = None
        self.superClassName = None
        self.implementClassName = []
        
        self.register = {}
        self.local = {}
        self.classes = []
        self.outputMethod = []
        self.outputClass = []
        
        self.curLabel = None
        
        self.switchMode = False
        self.switchBase = 0
        
        
        self.invokeRet = None
        self.invokeInfo = None
        
        #V void - Z boolean B byte S short C char I int J long F float D double     
        self.flags = {}
        self.flags['V'] = 'void'
        self.flags['Z'] = 'boolean'
        self.flags['B'] = 'byte'
        self.flags['S'] = 'short'
        self.flags['C'] = 'char'
        self.flags['I'] = 'int'
        self.flags['J'] = 'long'
        self.flags['F'] = 'float'
        self.flags['D'] = 'double'
        
        self.compare = {}
        self.compare['eq'] = '=='
        self.compare['ne'] = '!='
        self.compare['lt'] = '<'
        self.compare['ge'] = '>='
        self.compare['gt'] = '>'
        self.compare['le'] = '<='
        
        self.calculate = {}
        self.calculate['add'] = '+'
        self.calculate['sub'] = '-'
        self.calculate['mul'] = '*'
        self.calculate['div'] = '/'
        self.calculate['rem'] = '%'
        self.calculate['and'] = '&'
        self.calculate['or'] = '|'
        self.calculate['xor'] = '^'
        self.calculate['shl'] = '<<'
        self.calculate['shr'] = '>>'
        self.calculate['ushr'] = '>>>'
        
        self.calculate['not'] = '!'
        self.calculate['neg'] = '-'
        
        self.outputShift = 1
        
        self.createMethod = False
        self.annotationMode = False
        
        pass

    def debug(self, string):
        print string
        pass
        
    def resetRegister(self):
        self.register = {}
        self.local = {}
        self.switchInfo = {}
        
    def getRegister(self, reg):
        if self.register.has_key(reg):
            return self.register[reg]
        else:
            return reg
            
    def setRegister(self, reg, value, local = None):
        
        skip = self.local.has_key(reg) and self.local[reg] == True
        if (not skip) or local != None:
            self.register[reg] = value
        else:
            var = self.getRegister(reg)
            self.appendMethodToFile(var + ' = ' + value)

        if local == True:
            self.local[reg] = True
        elif local == False:
            self.local[reg] = False
    
    
    def appendClassToFile(self, string):
        self.outputClass.append(string)
        
    def appendMethodToFile(self, string, line = None):
        if line == None:
            line = self.outputShift
        for i in range(line):
            string = '\t' + string
        self.outputMethod.append(string)
    
    def getMethodCount(self):
        return len(self.outputMethod)
    
    def insertMethodToFile(self, string, pos, line = None):
        if line == None:
            line = self.outputShift
        for i in range(line):
            string = '\t' + string
        self.outputMethod.insert(pos, string)        
    
    def outputToFile(self, file = None):
        #print '--------------------------------'
        for string in self.outputClass:
            if file != None:
                file.write(string +'\n')
            #print string
        for string in self.outputMethod:
            if file != None:
                file.write(string + '\n')
            #print string 
            
    def doTranslate(self, line):
        line = line.strip()
        
        if len(line)!=0:
            #print line
            if (line[0] ==  '.'):
                self.doDot(line)
            elif (self.annotationMode == True):
                pass
            elif self.switchMode == True:
                self.doSwitchCase(line)
            elif (line[0] == ':'):
                self.doLabel(line)
            elif (line[0] == '#'):
                self.doCommit(line)
            else:
                self.doCommand(line)

    def doTranslateEnd(self):
        
        classes = set(self.classes)
        
        for c in classes:
            string = 'import ' + c
#            if c != '':
            self.appendClassToFile(string)
        
        string = 'class '
        
        for typed in self.classType:
            string = string + typed + ' '
        string = string + self.className
        
        if self.superClassName != None:
            string = string + ' extends ' + self.superClassName
        
        if len(self.implementClassName) != 0:
            string = string + ' implement '
            for i in range(len(self.implementClassName)):
                c = self.implementClassName[i]
                if (i != len(self.implementClassName)-1):
                    string = string + c + ', '
                else:
                    string = string + c
            
        string = string + '{'
        self.appendClassToFile(string)

    def makeParamsClass(self, part):
        cs = []
        obj = False
                
        for i in range(len(part)):
            if obj == False:
                if (part[i] == '['):
                    obj = True
                    start = i
                elif (part[i] == 'L'):
                    obj = True
                    start = i
                else:
                    cs.append(self.flags[part[i]])
            else:
                if (part[i] == ';'):
                    c = part[start:i+1]
                    c = self.makeClass(c)
                    cs.append(c)
                    obj = False
        return cs


    def makeParamsClass2String(self, params):
        string = ''
        offset = 1
        if self.functionStatic == True:
            offset = 0
            
        for i in range(len(params)):
            param = params[i]
            if (i != len(params)-1):
                string = string + param + ' ' + self.getRegister('p' + str(i + offset)) + ','
            else:
                string = string + param + ' ' + self.getRegister('p' + str(i + offset))
        return string                    
        


    def doDot(self, line):
        if line[1:5] == 'line':
            part = line.split()
            number = part[1]
            self.appendMethodToFile('// line ' + number, 0)
        elif line[1:6] == 'class':
            part = line.split()
            self.className = self.makeClass(part[-1], False)
            self.classType = []
            for i in range(1, len(part)-1):
                self.classType.append(part[i])
        elif line[1:6] == 'super':
            # .super Landroid/text/TextWatcher;
            part = line.split()
            self.superClassName = self.makeClass(part[-1])
        elif line[1:11] == 'implements':
            # .implements Landroid/text/TextWatcher;
            part = line.split()
            self.implementClassName.append(self.makeClass(part[-1]))
            
        elif line[1:6] == 'field':
            # .field private static final COLUMN_INDEX_FIRST:I = 0x0
            part = line.split('=')

            part1 = part[0].strip().split()
            part2 = part1[-1].split(':')
            field = part2[0]
            fieldClass = self.makeClass(part2[1])

            string = ''
            
            for i in range(1, len(part1)-1):
                string = string + part1[i] + ' '
                
            string = string + fieldClass + ' ' + field
            if len(part) > 1:
                value = part[1].strip()
                string = string + ' = ' + value
            self.appendMethodToFile(string)

        elif line[1:10] == 'end field':
            pass
        elif line[1:7] == 'method':
            # .method public static main([Ljava/lang/String;)V
            part = line.split()
            part2 = part[-1].split('(')
            part3 = part2[1].split(')')
            self.functionName = part2[0]
            self.functionParams = self.makeParamsClass(part3[0])
            self.functionRet = self.makeClass(part3[1])
            self.functionType = []
            #self.functionStatic = False
            self.functionParameter = 1
            self.functionStatic = False
            for i in range(1, len(part)-1):
                self.functionType.append(part[i])
                if part[i] == 'static':
                    #self.functionStatic = True
                    self.functionParameter = 0
                    self.functionStatic = True
            
            self.resetRegister()
            self.setRegister('p0', 'this')
            self.createMethod = True
            
        elif line[1:10] == 'parameter':
            # .parameter "x0"
            part = line.split()
            if len(part) > 1:
                para = part[1][1:-1]
                self.setRegister('p' + str(self.functionParameter), para)
                self.functionParameter = self.functionParameter + 1

        elif line[1:9] == 'prologue':
            self.doPrologue(line)
            self.createMethod = False
        elif line[1:11] == 'end method':
            if self.createMethod == True:
                self.doPrologue(line)
                self.createMethod = False
            self.outputShift = self.outputShift - 1
            string = '}'
            string = string + '//:end method::'
            self.appendMethodToFile(string)
            #self.resetRegister()

        elif line[1:7] == 'locals':
            pass
        elif line[1:6] == 'local' or line[1: 14] == 'restart local':
            # .local v0, bundle:Landroid/os/Bundle;
            line = line.replace(',',' ')
            part = line.split()
            if line[1:8] == 'restart':
                del part[0]
            
            if len(part) > 2:
                part2 = part[2].split(':')
                var = part2[0]
                if var[0] == '#':
                    var = var[1:]
                reg = part[1]
                c = self.makeClass(part2[1])            
                value = self.getRegister(reg)
                string = c + ' ' + var + ' = ' + value + '    /* <code> */'
                self.setRegister(reg, var, True)
                #n = self.invokeInfo
                #self.insertMethodToFile(string, n)
                self.appendMethodToFile(string)

            pass
        elif line[1:10] == 'end local':
            # .end local v0           #cityName:Ljava/lang/String;
            part = line.split()
            reg = part[2]
            self.setRegister(reg, reg, False)
            
            pass

        elif line[1:11] == 'annotation':
            self.annotationMode = True
        elif line[1:15] == 'end annotation':
            self.annotationMode = False
            pass
        elif line[1:14] == 'sparse-switch' or line[1:14] == 'packed-switch':
            # .sparse-switch
            # .packed-switch 0x1
            part = line.split()
            if len(part) == 2:
                self.switchBase = int(part[1], 16)
            self.switchMode = True
            self.outputShift = self.outputShift + 1
        elif line[1:18] == 'end sparse-switch' or line[1:18] == 'end packed-switch':
            self.switchMode = False
            self.outputShift = self.outputShift - 1
            n = self.switchInfo[self.curLabel]
            string = '}'
            self.insertMethodToFile(string, n)            
        elif line[1:6] == 'catch':
            # .catch Ljava/lang/Exception; {:try_start_7 .. :try_end_7} :catch_7
            part = line.split()
            if line[6:9] == 'all':
                c = None
                label = part[4][1:]
            else:
                c = self.makeClass(part[1])
                label = part[5][1:]
            if c != None:
                self.appendMethodToFile('catch (' + c + '){')
            else:
                self.appendMethodToFile('catch (){')
            self.outputShift = self.outputShift + 1
            self.appendMethodToFile('goto ' + label)
            self.outputShift = self.outputShift - 1
            self.appendMethodToFile('}')
            
        elif line[1:7] == 'source':
            pass
        else:
            self.debug('<error dot>' + line)


    def doPrologue(self, line):
        # .prologue
        if self.functionName == '<init>':
            self.functionName = self.className
        
        string = ''
        for typed in self.functionType:
            string = string + typed + ' '            
            
        string = string + self.functionRet + ' ' + self.functionName + '('
        string = string + self.makeParamsClass2String(self.functionParams) + '){'
        string = string + ' //:start method::' + self.functionName
        self.appendMethodToFile(string)
        self.outputShift = self.outputShift + 1    
            

    def doLabel(self, line):
        # :cond_1
        label = line[1:]
        self.curLabel = label
        
        if label[0:10] == 'try_start_':
            string = 'try {'
            self.appendMethodToFile(string)
            self.outputShift = self.outputShift + 1
        elif label[0:8] == 'try_end_':
            string = '}'
            self.outputShift = self.outputShift - 1    
            self.appendMethodToFile(string)
        else:
            string = ':' + label
            string = string + ' //:label::'+label
            self.appendMethodToFile(string, 1)
    
    def doCommit(self, line):
        #self.appendMethodToFile('//' + line)
        pass
    
    def doCommand(self, line):
        self.lineDelay = False
        
        if self.createMethod == True:
            self.doPrologue('.prologue')
            self.createMethod = False

        
        if line[0:6] == 'invoke':
            self.doInvoke(line)
        elif line[0:5] == 'const':
            self.doConst(line)
        elif line[0:4] == 'iget':
            self.doPutGet(line,'get')
        elif line[0:4] == 'iput':
            self.doPutGet(line,'put')
        elif line[0:4] == 'sget':
            self.doStaticPutGet(line,'get')
        elif line[0:4] == 'sput':
            self.doStaticPutGet(line,'put')
        elif line[0:4] == 'aget':
            self.doArrayPutGet(line,'get')
        elif line[0:4] == 'aput':
            self.doArrayPutGet(line,'put')            
        elif line[0:4] == 'move':
            self.doMove(line)
        elif line[0:6] == 'return':
            self.doReturn(line)
        elif line[0:4] == 'goto':
            self.doGoto(line)
        elif line[0:3] == 'new':
            self.doNew(line)
        elif line[0:2] == 'if':
            self.doIf(line)
        elif line[0:5] == 'check':
            self.doCheck(line)
        elif line.find('-to-') > 0:
            self.doTo(line)
        elif line[0:3] == 'add' or line[0:3] == 'sub' or line[0:3] == 'mul' or line[0:3] == 'div' or line[0:3] == 'rem' or line[0:3] == 'and' or line[0:2] == 'or' or line[0:3] == 'xor' or line[0:3] == 'shl' or line[0:3] == 'shr' or line[0:4] == 'ushr':
            self.doCalculate(line)
        elif line[0:3] == 'not' or line[0:3] == 'neg':
            self.doCalculate2(line)
        elif line[0:3] == 'cmp':
            self.doCmp(line)
        elif line[0:13] == 'sparse-switch' or line[0:13] == 'packed-switch':
            self.doSwitch(line)
            pass
        elif line[0:12] == 'array-length':
            self.doArray(line)
        elif line[0:5] == 'throw':
            self.doThrow(line)
        elif line[0:11] == 'instance-of':
            self.doInstanceOf(line)
        elif line[0:3] == 'nop':
            pass
        elif line[0:7] == 'monitor':
            self.doMonitor(line)
        else:
            # execute-inline
            # invoke-virtual/range {vx..vy},methodtocall
            # filled-new-array {parameters},type_id
            # monitor-enter vx
            # const-class vx,type_id
            self.debug('<error> command:' + line)
            
        if self.lineDelay == False:
            if self.invokeRet != None:
                n = self.invokeInfo
                self.insertMethodToFile(self.invokeRet, n)
                self.invokeRet = None


    def makeClass(self, part, add = True):
        ret = '<error>'
        obj = False
        array = False
        for i in range(len(part)):
            if obj == False:
                if (part[i] == '['):
                    array = True
                elif (part[i] == 'L'):
                    obj = True
                    start = i
                else:
                    ret = (self.flags[part[i]])
                    add = False
                    break
            else:
                if (part[i] == ';'):
                    c = part[start+1:i]
                    c = c.replace('/', '.')

                    ret = (c)
                    break
        if add == True:
            self.classes.append(ret)
        
        ret = ret.split('.')[-1]
        
        if array == True:
            ret = (ret + '[]')
        
        return ret

    def makeFunction(self, part):
# part : Landroid/app/Activity;->onCreate(Landroid/os/Bundle;)V
        start = part.find('>') + 1
        end = part.find('(')
        
        function = part[start:end]    
        if function == '<init>':
            part2 = part.split(';')
            c = self.makeClass(part2[0]+';')
            function = c
        
        return function    


    def makeParams(self, part):
# part : {p0, p1},
        part = part.replace('{', '')
        part = part.replace('}', '')
        part = part.replace(' ', '')
        
        params = part.split(',')
        #del params[-1]
        if params[0] == '':
            return []
        for i in range(len(params)):
            params[i] = self.getRegister(params[i])
        return params

    def makeField(self, part):
        # Lcom/tutor/apkinstaller/ApkInstaller;->apkWeb:Landroid/webkit/WebView;
        start = part.find('>') + 1
        end = part.find(':')
        
        return part[start:end]         

    def makeParams2String(self, params):
        string = ''
        for i in range(len(params)):
            param = params[i]
            if (i != len(params)-1):
                string = string + param + ', '
            else:
                string = string + param
        return string


        
    def doInvoke(self, line):
        line = line.replace(', ', ',')
        part = line.split('},')
        part2 = part[0].split()
        function = self.makeFunction(part[1])
        params = self.makeParams(part2[1])
        retClass = line.split(')')[-1]
        
        showRet = False
        if retClass != 'V':
            showRet = True

        string = None
        if line[6:12] == '-super':
            # invoke-super {p0, p1}, Landroid/app/Activity;->onCreate(Landroid/os/Bundle;)V  
            string = 'super.' + function + '('
            del params[0]
            string = string + self.makeParams2String(params)
            string = string + ')'
            self.invokeRet = string
        elif line[6:13] == '-direct':
            # invoke-direct {v0}, Ljava/lang/RuntimeException;-><init>()V
            funClass = self.makeClass(part[1])
            
            if funClass == function: #(params[0][0:4] == 'new ' and 
                pass
            else:
                string = funClass + '.' + params[0] + '.' + function + '('
                del params[-1]
                string = string + self.makeParams2String(params)
                string = string + ')'
            self.invokeRet = string    
        elif line[6:13] == '-static':
            # invoke-static {p1}, Landroid/text/TextUtils;->isEmpty(Ljava/lang/CharSequence;)Z
            part3 = part[1].split(';')
            function_class = self.makeClass(part3[0]+';')
            string = function_class + '.' + function + '('
            string = string + self.makeParams2String(params)
            string = string + ')'
            self.invokeRet = string
        elif line[6:14] == '-virtual' or line[6:16] == '-interface':
            # invoke-virtual {v2, v0}, Landroid/webkit/WebView;->loadUrl(Ljava/lang/String;)V
            obj = params[0]
            string = obj + '.' + function + '('
            del params[0]
            string = string + self.makeParams2String(params)
            string = string + ')'
            self.invokeRet = string
        else:
            self.debug('<error> invoke :' + line)
        if self.invokeRet != None:
            if showRet == False:
                self.appendMethodToFile(self.invokeRet)
                self.invokeRet = None
            else:
                self.invokeInfo = self.getMethodCount()
                self.lineDelay = True

    def doConst(self, line):
        # const/high16 v2, 0x7f03
        # const-string v2, ", "
        part = line.split(',', 1)
        part2 = part[0].split()
        
        var = part2[1]
        value = part[1].strip()
#        if value[0] == '-':
#            value = '(' + value + ')'
        self.setRegister(var, value)
        pass   

        
    def doPutGet(self, line, pg):
        # iput-object v2, p0, Lcom/tutor/apkinstaller/ApkInstaller;->apkWeb:Landroid/webkit/WebView;  
        line = line.replace(', ', ',')
        part = line.split()
        part2 = part[1].split(',')
        field = self.makeField(part2[2])
        obj  = part2[1]
        value = part2[0]

        if pg == 'put':
            value = self.getRegister(value)
            obj = self.getRegister(obj)
            string = obj + '.' + field + ' = ' + value
            self.appendMethodToFile(string)
        elif pg == 'get':
            obj = self.getRegister(obj)
            self.setRegister(value, obj + '.' + field)

    def doStaticPutGet(self, line, pg):
        # sput-object v1, Lcom/moji/mjweather/activity/AddCityActivity;->mHotCitys:[Ljava/lang/String;
        line = line.replace(', ', ' ')
        part = line.split()
        field = self.makeField(part[2])  
        obj  = 'p0'
        value = part[1]

        if pg == 'put':
            value = self.getRegister(value)
            obj = self.getRegister(obj)
            string = obj + '.' + field + ' = ' + value
            self.appendMethodToFile(string)
        elif pg == 'get':
            obj = self.getRegister(obj)
            self.setRegister(value, obj + '.' + field)

    def doArrayPutGet(self, line, pg):
        # aget-object v3, v3, v0
        line = line.replace(', ', ' ')
        part = line.split()
        
        value = part[1]
        obj = self.getRegister(part[2]) 
        aid = self.getRegister(part[3])  


        if pg == 'put':
            value = self.getRegister(value)
            obj = self.getRegister(obj)
            string = obj + '[' + aid + '] = ' + value
            self.appendMethodToFile(string)
        elif pg == 'get':
            obj = self.getRegister(obj)
            self.setRegister(value, obj + '[' + aid + ']')
            
    def doMove(self, line):
        if line[4:11] == '-result':
        # move-result-object v2
            part = line.split()
            ret = part[1]
            self.setRegister(ret, self.invokeRet)
            self.invokeRet = None
            pass
        elif line[4:14] == '-exception':
            pass
        else:
        # move-object/from16 v0, p0    
            line = line.replace(', ', ' ')
            part = line.split()
            var = part[1]
            value = self.getRegister(part[2])
            self.setRegister(var, value)
        
        
    def doReturn(self, line):
        if line[6:11] == '-void':
            # return-void
            string = 'return;'
            string = string + ' //:return::'
            self.appendMethodToFile(string)
        else:
            part = line.split()
            
            if (len(part) > 1):
                ret = part[1]
                ret = self.getRegister(ret)
                string = 'return ' + ret +';'
                string = string + ' //:return::'
                self.appendMethodToFile(string)
    
    def doGoto(self, line):
        part = line.split(':')
        label = part[1]
        string = 'goto '
        string = string + label
        string = string + ' //:goto::' + label
        self.appendMethodToFile(string)
    
    def doNew(self, line):
        line = line.replace(',', '')
        part = line.split()
        if line[3:12] == '-instance':
        # new-instance v1, Lcom/moji/mjweather/activity/AddCityActivity$1;
            var = part[1]
            c = self.makeClass(part[2])
            self.setRegister(var, 'new ' + c + '()')
        elif line[3:9] == '-array':
        # new-array v1, v1, [Ljava/lang/String;
            var = part[1]
            size = self.getRegister(part[2])
            c= self.makeClass(part[3])
            self.setRegister(var, 'new ' + c + '[' + size + ']')
            
    
    def doIf(self, line):
        line = line.replace(',', '')
        part = line.split()
        if line[5] == 'z':
        # if-nez v1, :cond_0
            c0 = self.getRegister(part[1])
            c1 = '0'
            label = part[2][1:]
        else:
        # if-ge v0, v1, :cond_1
            c0 = self.getRegister(part[1])
            c1 = self.getRegister(part[2])
            label = part[3][1:]

        compare = self.compare[part[0][3:5]]
        
        string = 'if (' + c0 + ' ' + compare + ' ' + c1 + '){'
        self.appendMethodToFile(string)
        self.outputShift = self.outputShift + 1
        string = 'goto ' + label + ';'
        self.appendMethodToFile(string)
        self.outputShift = self.outputShift - 1
        string = '}'
        self.appendMethodToFile(string)
        
    def doCheck(self, line):
        # check-cast v1, Landroid/widget/ImageButton;
        line = line.replace(',', '')
        part = line.split()
        var = part[1]
        obj = self.getRegister(var)
        c = self.makeClass(part[2])
        self.setRegister(var, '(' + c + ')' + obj)
        
        pass
    
    def doCalculate(self, line):
        # mul-double/2addr v3, v5
        line = line.replace(',', ' ')
        part = line.split()
        part2 = part[0].split('-')
        
        if part[0].find('2addr') > 0:
            ret = part[1]
            p1 = self.getRegister(part[1])
            p2 = self.getRegister(part[2])
        elif part[0].find('lit') > 0:
        #add-int/lit8 v9, v8, 0x1
            ret = part[1]
            p1 = self.getRegister(part[2])
            p2 = part[3]
#            if p2[0] == '-':
#                p2 = '('+p2+')'        
        else:
            ret = part[1]
            p1 = self.getRegister(part[2])
            p2 = self.getRegister(part[3])
            
        calculate = self.calculate[part2[0]]
        if calculate == '+' and p2[0] == '-':
            calculate = '-'
            p2 = p2[1:]        
        
        self.setRegister(ret, '(' + p1 + ' ' + calculate + ' ' + p2 + ')')

    def doCalculate2(self, line):
        # not-int vx, vy
        line = line.replace(',', ' ')
        part = line.split()
        part2 = part[0].split('-')
        
        var = part[1]
        value = self.getRegister(part[2])
        calculate = self.calculate[part2[0]]

        self.setRegister(var, '(' + calculate + value + ')')


    def doCmp(self, line):
        #cmpl-float v13, v11, v7
        line = line.replace(',', ' ')
        part = line.split()
        reg = part[1]
        value1 = self.getRegister(part[2])
        value2 = self.getRegister(part[3])
        self.setRegister(reg, '(' + value1 + '>' + value2 + '?1:' + value1 + '<' + value2 + '?-1:0)')
        
        

    def doSwitch(self, line):
        # sparse-switch v1, :sswitch_data_0
        # packed-switch p0, :pswitch_data_0
        line = line.replace(',', ' ')
        part = line.split()
        
        var = self.getRegister(part[1])
        data = part[2][1:]
        
        string = 'switch (' + var + ')' + '{'
        
            
        self.appendMethodToFile(string)
        self.switchInfo[data] = self.getMethodCount() + 1
    
    def doSwitchCase(self, line):
        line = line.replace(' ', '')
        part = line.split('->')
        
        if len(part) == 2:
            # 0x1 -> :sswitch_0
            value = part[0]
            label = part[1][1:]

        else:
            # :pswitch_0
            value = str(self.switchBase)
            self.switchBase = self.switchBase + 1
            label = part[0][1:]
            
        n = self.switchInfo[self.curLabel]
        string = 'case ' +     value + ': ' + 'goto ' + label
        self.insertMethodToFile(string, n)
        self.switchInfo[self.curLabel] = n + 1    

    def doArray(self, line):
        # array-length v1, v1
        line = line.replace(',', ' ')
        part = line.split()
        ret = part[1]
        obj = self.getRegister(part[2])
        self.setRegister(ret, obj + '.length()')
        
    
    def doTo(self, line):
        # int-to-double v3, v3
        line = line.replace(',', '')
        part = line.split()
        part2 = part[0].split('-to-')
        f = part[1]
        t = part[2]
        f = self.getRegister(f)
        self.setRegister(t, '(' + part2[1] + ')' + f)
        pass
    
    def doThrow(self, line):
        # throw v0
        part = line.split()
        value = self.getRegister(part[1])
        string = 'throw ' + value
        self.appendMethodToFile(string)
        
    def doInstanceOf(self, line):
        # instance-of v8, v7, Landroid/widget/TextView;
        line = line.replace(',', '')
        part = line.split()
        reg = part[1]
        value = self.getRegister(part[2])
        c = self.makeClass(part[3])
        
        self.setRegister(reg, '(' + value + ' instanceof ' + c + ')')
        pass

    def doMonitor(self, line):
        #monitor-enter p0
        part = line.split()
        obj = self.getRegister(part[1])
        if line[7:13] == '-enter':
#            string = 'synchronized(' + obj + '){'
#            self.appendMethodToFile(string)
#            self.outputShift = self.outputShift + 1
            pass
        elif line[7:12] == '-exit':
#            self.outputShift = self.outputShift - 1
#            string = '}'
#            self.appendMethodToFile(string)
            pass
        else:
            self.debug('<error monitor> ' + line)
        

def listfile(dirname):
    files = []
    try:
        ls=os.listdir(dirname)
    except:
        print 'dir access deny'
    else:
        for l in ls:
            filename = os.path.join(dirname,l)
            if(os.path.isdir(filename)):
                filenames = listfile(filename)
                for filename in filenames:
                    files.append(filename)
            else:
                files.append(filename)
                
    return files        

def smaliToJava(smali, java):
    fileSmali = open(smali)
    fileJava = open(java, 'w')
    
    sm = smali2java()
    
    for line in fileSmali.readlines():
        #try:
            sm.doTranslate(line)
        #except:
        #    pass
    sm.doTranslateEnd()
    sm.outputToFile(fileJava)
    fileSmali.close()    
    
if __name__ == "__main__":
    if len(sys.argv) == 2:
        dirs = sys.argv[1]
    else:
        print 'smali2java <dir>'
        print 'version: 1.00'
        exit()
        
    lists = listfile(dirs)
    
    for smali in lists:
        if smali[-6:] == '.smali':
            print 'FileName:' + smali
            java = smali.replace('.smali', '.java')
            smaliToJava(smali, java)
            

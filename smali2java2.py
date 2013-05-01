#import re
import os
import sys
import string
import struct



class javaOp():
    def __init__(self, op):
        self.op = op
        self.output = None
        self.type = None
        self.input = []
        self.label = None
        self.line = None
        self.lineEnd = False
        self.local = None # [reg, type, localName, restart]
        self.localEnd = [] 
        
        pass
    
    def setOutput(self, output):
        self.output = output
    
    def setType(self, type):
        self.type = type
    
    def addInput(self, input):
        self.input.append(input)
        
    def setInput(self, input):
        self.input = input

    def setLabel(self, label):
        self.label = label

    def setLine(self, line):
        self.line = line

    def setLineEnd(self, end):
        self.lineEnd = end

    def isLineEnd(self):
        return self.lineEnd

    def setLocal(self, c, var, mode = None):
        self.local = [c, var, mode]

    def isLocal(self):
        if self.local != None:
            return True
        return False

    def setLocalEnd(self, reg):
        self.localEnd.append(reg)

    def getLocalEnd(self):
        return self.localEnd

class javaField():
    def __init__(self, name, type, value = None):
        self.name = name
        self.type = type
        self.attr = []
        self.value = value
    
    def addAttr(self, attr):
        self.attr.append(attr)

class javaSwitch():
    def __init__(self):
        self.case = []
    
    def addCase(self, name, label):
        self.case.append([name,label])
            
class javaLabel():
    def __init__(self, name):
        self.name = name
        self.catch = None
    
    def setStart(self, start):
        self.start = start
        
    def setEnd(self, end):
        self.end = end
    
    def setCatch(self, catch):
        self.catch = catch
        


class javaMethod():
    def __init__(self, name, retType = None):
        self.name = name
        self.attr = []
        self.retType = retType
        self.paramType = []
        self.param = []
        self.op = []
        self.label = {}
        self.switch = {}

        self.reg = javaRegister()
        self.curLine = None

        self.tryCatch = []

        self.local = []
        
        pass
    
    def addAttr(self, attr):
        self.attr.append(attr)
    
    def addParamType(self, type):
        self.paramType.append(type)
    
    def addParam(self, name):
        self.param.append(name)
    
    def addOp(self, op):
        self.op.append(op)
    
    def addSwitch(self, name, data):
        self.switch[name] = data

    def addLabel(self, name, data):
        self.label[name] = data

    def getLabel(self, name):
        return self.label[name]

    def getOpCount(self):
        return len(self.op)

    def setTryCatch(self, labelStart, labelEnd, expClass, labelCatch):
        self.tryCatch.append([labelStart, labelEnd, expClass, labelCatch])

    def getTryCatch(self, labelEnd):
        for tryCatch in self.tryCatch:
            if tryCatch[1] == labelEnd:
                return tryCatch
        return None
    
    def isTryLabel(self, label):
        for tryCatch in self.tryCatch:
            if tryCatch[0] == label:
                return True
            if tryCatch[1] == label:
                return False
        return None

    def addLocal(self, ctype, var):
        for local in self.local:
            if local[1] == var:
                return
        self.local.append([ctype, var])

    
class javaClass():
    def __init__(self, name):
        self.name = name
        self.super = None
        self.attr = []
        self.implement = []
        self.method = []
        self.field = []
        pass
    
    def setSuper(self, name):
        self.super = name

    def addAttr(self, attr):
        self.attr.append(attr)

    def addImplement(self, name):
        self.implement.append(name)
    
    def addField(self, name, type, value = None):
        field = javaField(name, type, value)
        self.field.append(field)
        return field
    
    def addMethod(self, method):
        self.method.append(method)

class javaRegister():
    def __init__(self):
        self.register = {}
        self.local = {}
        self.const = {}   

    def getRegister(self, reg):
        if self.register.has_key(reg) and self.register[reg] != None:
            return self.register[reg]
        else:
            return reg
    def getRegisters(self, regs):
        tregs = []
        for reg in regs:
            tregs.append(self.getRegister(reg))
        return tregs
    
    def setRegister(self, reg, value, local = None, const = False):
        if not self.isLocal(reg) or local != None:
            self.register[reg] = value
            self.const[reg] = const

        if local == True:
            self.local[reg] = True
        elif local == False:
            self.local[reg] = False

    def clearRegister(self):
        for key in self.register.iterkeys():
            if (not (self.isLocal(key) or self.isConst(key))):
                self.register[key] = key

    def getLocal(self, reg):
        if reg == None:
            return None
        if self.isLocal(reg):
            local = self.getRegister(reg)
            return local
        return reg

    def isLocal(self, reg):
        if not self.local.has_key(reg):
            return False
        if self.local[reg] == False:
            return False
        return True

    def isConst(self, reg):
        if not self.const.has_key(reg):
            return False
        if self.const[reg] == False:
            return False
        return True


class smali2java2():
    
    def __init__(self):
        

        self.importClass = []

        self.switchBase = 0
        
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

        self.reCompare = {}
        self.reCompare['eq'] = '!='
        self.reCompare['ne'] = '=='
        self.reCompare['lt'] = '>='
        self.reCompare['ge'] = '<'
        self.reCompare['gt'] = '<='
        self.reCompare['le'] = '>'
        
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
        
        self.outputShift = 0
        
        self.annotationMode = False
        self.arrayDataMode = False
        
        self.javaOp = None
        self.javaOps = None
        self.registers = None
        self.javaClass = None
        self.javaMethod = None
        self.javaSwitch = None
        self.javaLabel = None

        self.curLabel = None
        self.curLine = None
        
        self.lineInfoEnable = True
        self.localInfoEnable = True
        
        self.access = {}
        self.javaAccess = None
        self.curAccess = None

    def debug(self, string):
        print string
        pass

    def appendMethodToFile(self, string, line = None):
        pass   
    
    def outputToFile(self, file = None):
        self.outputFile = file

        classes = set(self.importClass)
        
        for c in classes:
            string = 'import ' + c
#            if c != '':
            self.toFile(string)


        string = 'class '
        #for attr in self.javaClass.attr:
        #    string = string + attr + ' '
        string = string + self.javaClass.name
        if self.javaClass.super != None:
            string = string + ' extends ' + self.javaClass.super
        if len(self.javaClass.implement) != 0:
            string = string + ' implement '
            for i in range(len(self.javaClass.implement)):
                if len(self.javaClass.implement) == i + 1:
                    string = string + self.javaClass.implement[i]
                else:
                    string = string + self.javaClass.implement[i] + ', '
        self.toFile(string)
        
        string = '{'
        self.toFile(string)            
        
        self.toFileShift(1)
        
        for field in self.javaClass.field:
            string = ''
            for attr in field.attr:
                string = string + attr + ' '
            string = string + field.type + ' ' + field.name
            if field.value != None:
                string = string + ' = ' + field.value
            string = string + ';'
            
            self.toFile(string)     
        
        for i in range(len(self.javaClass.method)):
            self.outputMethodOp(i)
        self.toFileShift(-1)

        string = '}'
        self.toFile(string)

        self.outputFile = None
            
    def doTranslate(self, line):
        line = line.strip()
        
        if len(line)!=0:
            if (line[0] ==  '.'):
                self.doDot(line)
            elif (self.annotationMode == True):
                pass
            elif (self.arrayDataMode == True):
                if self.javaLabel == None:
                    exit()
                pass
            elif self.javaSwitch != None:
                self.doSwitchCase(line)
            elif (line[0] == ':'):
                self.doLabel(line)
            elif (line[0] == '#'):
                self.doCommit(line)
            else:
                self.doCommand(line)

    def makeClass(self, part, add = True):
        ret = '<error>'
        obj = False
        array = 0
        for i in range(len(part)):
            if obj == False:
                if (part[i] == '['):
                    array = array + 1
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
            self.importClass.append(ret)
        
        ret = ret.split('.')[-1]
        
        while array > 0:
            ret = (ret + '[]')
            array = array - 1
        
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
# part : p0,p1
# part : v0..v5
        if (part.find('..')>0):
            rMode = True
        else:
            rMode = False
        #part = part.replace('{', '')
        #part = part.replace('}', '')
        part = part.replace(',', ' ')
        part = part.replace('..', ' ')
       
        params = part.split()
        if rMode == False:
            if len(params) == 0 or params[0] == '':
                return []
            return params
        else:
            param2s = []
            vp = params[0][0]
            st = int(params[0][1:])
            end = int(params[1][1:]) + 1
            for i in range(st,end):
                param2s.append(vp + str(i))
            return param2s
        

    def makeField(self, part):
        # Lcom/tutor/apkinstaller/ApkInstaller;->apkWeb:Landroid/webkit/WebView;
        start = part.find('>') + 1
        end = part.find(':')
        
        return part[start:end]

    def makeParamsClass(self, part):
        cs = []
        obj = False
        array = 0
                
        for i in range(len(part)):
            if obj == False:
                if (part[i] == '['):
                    array = array + 1
                elif (part[i] == 'L'):
                    obj = True
                    start = i
                else:
                    c = part[i-array:i+array+1]
                    c = self.makeClass(c)
                    cs.append(c)
                    obj = False
                    array = 0
            else:
                if (part[i] == ';'):
                    c = part[start-array:i+1]
                    c = self.makeClass(c)
                    cs.append(c)
                    obj = False
                    array = 0
        return cs


    def doDot(self, line):
        if line[1:5] == 'line':
            part = line.split()
            number = part[1]
            if self.curLine != None and self.javaOp != None:
                self.javaOp.setLineEnd(True)
                #self.javaOp = None
            self.curLine = number

        elif line[1:6] == 'class': # fix
            part = line.split()
            name = self.makeClass(part[-1], False)
            self.javaClass = javaClass(name)

            for i in range(1, len(part)-1):
                attr = part[i]
                self.javaClass.addAttr(attr)
                
        elif line[1:6] == 'super': # fix
            # .super Landroid/text/TextWatcher;
            part = line.split()
            name = self.makeClass(part[-1])
            
            self.javaClass.setSuper(name)
            
        elif line[1:11] == 'implements': # fix
            # .implements Landroid/text/TextWatcher;
            part = line.split()
            name = self.makeClass(part[-1])
            self.javaClass.addImplement(name)
            
        elif line[1:6] == 'field': # fix
            # .field private static final COLUMN_INDEX_FIRST:I = 0x0
            part = line.split('=')

            part1 = part[0].strip().split()
            part2 = part1[-1].split(':')
            field = part2[0]
            fieldClass = self.makeClass(part2[1])
            if len(part) == 2:
                value = part[1].strip()
            else:
                value = None 

            v = self.javaClass.addField(field, fieldClass, value)
            string = ''
            
            for i in range(1, len(part1)-1):
                attr = part1[i]
                v.addAttr(attr)
                #self.javaClass.addAttr(attr)

        elif line[1:10] == 'end field': # fix
            pass
        elif line[1:7] == 'method': # fix
            # .method public static main([Ljava/lang/String;)V
            part = line.split()
            part2 = part[-1].split('(')
            part3 = part2[1].split(')')
            if part2[0] != '<init>':
                functionName = part2[0]
            else:
                functionName = self.javaClass.name
            functionTypes = self.makeParamsClass(part3[0])
            functionRet = self.makeClass(part3[1])

            self.javaMethod = javaMethod(functionName, functionRet)
            self.javaClass.addMethod(self.javaMethod)
            
            for i in range(1, len(part)-1):
                attr = part[i]
                self.javaMethod.addAttr(attr)
                
            for tpye in functionTypes:
                self.javaMethod.addParamType(tpye)

            self.javaOp = None
            self.javaOps = {}
            self.registers = {}
            
        elif line[1:10] == 'parameter': # fix
            # .parameter "x0"
            part = line.split()
            if len(part) > 1:
                para = part[1][1:-1]
                self.javaMethod.addParam(para)

        elif line[1:9] == 'prologue': # fix
            pass
        elif line[1:11] == 'end method': # fix
            self.javaMethod = None
            self.javaOp = None
            self.javaOps = None
            self.registers = None
            self.curLine = None
            self.curLabel = None

        elif line[1:7] == 'locals':
            pass
        elif line[1:6] == 'local' or line[1: 14] == 'restart local':
            # .local v0, bundle:Landroid/os/Bundle;
            line = line.replace(',',' ')
            part = line.split()
            mode = False
            if line[1:8] == 'restart':
                del part[0]
#                mode = True
            
            if len(part) > 2:
                part2 = part[2].split(':')
                var = part2[0]
                if var[0] == '#':
                    var = var[1:]
                reg = part[1]
                
                c = self.makeClass(part2[1])

                if reg[0:2] != 'p0':
                    if self.javaOp != None and (self.javaOp.output == reg or self.javaMethod.reg.getRegister(self.javaOp.output) == reg):
                        self.javaOp.setLocal(c, var, mode)
                        self.javaMethod.addLocal(c, var)
                    else:
                        if self.javaLabel != None and self.javaLabel.catch == reg:
                            self.javaLabel.catch = var

                        javaOpl = javaOp('nop')
                        javaOpl.setOutput(reg)
                        self.javaMethod.addOp(javaOpl)
                        javaOpl.setLocal(c, var, mode)
                        self.javaMethod.addLocal(c, var)
            pass
        elif line[1:10] == 'end local':
            # .end local v0           #cityName:Ljava/lang/String;
            part = line.split()
            reg = part[2]
            
            self.javaOp.setLocalEnd(reg)
            pass
        elif line[1:11] == 'array-data':
            self.arrayDataMode = True
        elif line[1:15] == 'end array-data':
            self.arrayDataMode = False
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

            self.javaSwitch = javaSwitch()
            self.javaMethod.addSwitch(self.javaLabel.name, self.javaSwitch)
            
        elif line[1:18] == 'end sparse-switch' or line[1:18] == 'end packed-switch':
            self.javaSwitch = None
        elif line[1:6] == 'catch':
            # .catch Ljava/lang/Exception; {:try_start_7 .. :try_end_7} :catch_7
            part = line.split()
            if line[6:9] == 'all':
                c = 'Exception'
            else:
                c = self.makeClass(part[1])
                del part[1]
            
            labelCatch = part[4][1:]
            labelTryStart = part[1][2:]
            labelTryEnd = part[3][1:-1]
            self.javaMethod.setTryCatch(labelTryStart, labelTryEnd, c, labelCatch)
            
            javaOpl = javaOp('catch')
            javaOpl.addInput(c)
            javaOpl.addInput(labelCatch)
            self.javaMethod.addOp(javaOpl)
        elif line[1:7] == 'source':
            pass
        else:
            self.debug('<error dot>' + line)
        

    def doLabel(self, line): # fix
        # :cond_1
        name = line[1:]

        self.curLabel = name
        self.javaLabel = javaLabel(name)
        self.javaMethod.addLabel(name, self.javaLabel)
        self.javaLabel.setStart(self.javaMethod.getOpCount())
     
        if self.curLine != None and self.javaOp != None:
            self.javaOp.setLineEnd(True)
#            self.javaOp = None
        javaOpl = javaOp('nop')
        self.javaMethod.addOp(javaOpl)   
        javaOpl.setLabel(self.curLabel)


    
    def doCommit(self, line):
        #self.appendMethodToFile('//' + line)
        pass
    
    def doCommand(self, line):
        if line[0:6] == 'invoke':
            self.doInvoke(line)
        elif line[0:5] == 'const':
            if (line[6:10] == 'wide'): # 64 bit
                self.doConst(line, 2)
            if (line[6:12]) == 'high16':
                self.doConst(line, 0) # 16 bit
            else:
                self.doConst(line, 1) # 32 bit
        elif line[0:4] == 'iget':
            self.doPutGet(line,'get')
        elif line[0:4] == 'iput':
            self.doPutGet(line,'put')
        elif line[0:4] == 'sget':
            self.doStaticPutGet(line,'sget')
        elif line[0:4] == 'sput':
            self.doStaticPutGet(line,'sput')
        elif line[0:4] == 'aget':
            self.doArrayPutGet(line,'aget')
        elif line[0:4] == 'aput':
            self.doArrayPutGet(line,'aput')            
        elif line[0:4] == 'move':
            self.doMove(line)
        elif line[0:6] == 'return':
            self.doReturn(line)
        elif line[0:4] == 'goto':
            self.doGoto(line)
        elif line[0:3] == 'new':
            self.doNew(line)
        elif line[0:15] == 'fill-array-data':
            self.doFillArray(line)
        elif line[0:2] == 'if':
            self.doIf(line)
        elif line[0:5] == 'check':
            self.doCheck(line)
        elif line.find('-to-') > 0:
            self.doTo(line)
        elif line[0:3] == 'add' or line[0:3] == 'sub' or line[0:3] == 'mul' or line[0:3] == 'div' or line[0:3] == 'rem' or line[0:3] == 'and' or line[0:2] == 'or' or line[0:3] == 'xor' or line[0:3] == 'shl' or line[0:3] == 'shr' or line[0:4] == 'ushr':
            self.doCalculate2(line)
        elif line[0:3] == 'not' or line[0:3] == 'neg':
            self.doCalculate(line)
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
            self.javaOp = javaOp('nop')
            self.javaMethod.addOp(self.javaOp)  
        elif line[0:7] == 'monitor':
            self.doMonitor(line)
        else:
            # execute-inline
            # invoke-virtual/range {vx..vy},methodtocall
            # filled-new-array {parameters},type_id
            # const-class vx,type_id
            self.debug('<error> command:' + line)
        
#        if self.curLabel != None and self.javaOp != None:
#            self.javaOp.setLabel(self.curLabel)
#            self.curLabel = None
        if self.javaOp != None and self.curLine != None:
            self.javaOp.setLine(self.curLine)
            #self.curLine = None

        
    def doInvoke(self, line):
        line = line.replace(', ', ',')
        line = line.replace(' .. ', '..')
        part = line.split('},')
        part2 = part[0].split()
        c = self.makeClass(part[1])
        function = self.makeFunction(part[1])
        params = self.makeParams(part2[1][1:])
        cs = self.makeParamsClass(part[1].split('(')[1].split(')')[0])
        #print cs
        
        s = 0
        if line[6:13] != '-static':
            s = 1
        
        for i in range(len(cs)):
            if cs[i] == 'double' or cs[i] == 'long':
                del params[i+1+s]
        #print params
        
        retClass = line.split(')')[-1]
        
        showRet = False
        if retClass != 'V':
            showRet = True

        string = None
        if line[6:12] == '-super': # fix
            # invoke-super {p0, p1}, Landroid/app/Activity;->onCreate(Landroid/os/Bundle;)V
            self.javaOp = javaOp('invoke')
            self.javaOp.addInput('super')
            self.javaOp.addInput(function)
            del params[0]
            #for param in params:
            #    self.javaOp.addInput(param)
            for i in range(len(cs)):
                self.javaOp.addInput(cs[i])
                self.javaOp.addInput(params[i])    
                
            self.javaOp.setType(retClass)
            self.javaMethod.addOp(self.javaOp)
            
        elif line[6:13] == '-direct': # fix
            # invoke-direct {v0}, Ljava/lang/RuntimeException;-><init>()V
            for i in range(len(params)):
                if self.registers != None and self.registers.has_key(params[i]):
                    params[i] = self.registers[params[i]]
            self.registers = None
            
            obj = params[0]
            
            if (self.javaOps.has_key(obj)):
                self.javaOp = javaOp('new-invoke')
                self.javaOp.setOutput(self.javaOps[obj].output)
                self.javaOp.setInput(self.javaOps[obj].input)
                #self.javaOp = self.javaOps[obj]
                #for i in range(1,len(params)):
                #    self.javaOp.addInput(params[i])
                del params[0]
                for i in range(len(cs)):
                    self.javaOp.addInput(cs[i])
                    self.javaOp.addInput(params[i])                      
                self.javaMethod.addOp(self.javaOp)
                del self.javaOps[obj]
            else:
                self.javaOp = javaOp('invoke')
                self.javaOp.addInput(params[0])
                self.javaOp.addInput(function)
                #for i in range(1,len(params)):
                #    self.javaOp.addInput(params[i])
                del params[0]
                for i in range(len(cs)):
                    self.javaOp.addInput(cs[i])
                    self.javaOp.addInput(params[i])       
                self.javaOp.setType(retClass)
                self.javaMethod.addOp(self.javaOp)                
                
        elif line[6:13] == '-static':
            # invoke-static {p1}, Landroid/text/TextUtils;->isEmpty(Ljava/lang/CharSequence;)Z
            part3 = part[1].split(';')
            functionClass = self.makeClass(part3[0]+';')
            
            self.javaOp = javaOp('invoke')
            self.javaOp.addInput(functionClass)
            self.javaOp.addInput(function)
            #for param in params:
            #    self.javaOp.addInput(param)
            for i in range(len(cs)):
                self.javaOp.addInput(cs[i])
                self.javaOp.addInput(params[i])       
            self.javaOp.setType(retClass)
            self.javaMethod.addOp(self.javaOp)
            
        elif line[6:14] == '-virtual' or line[6:16] == '-interface':
            # invoke-virtual {v2, v0}, Landroid/webkit/WebView;->loadUrl(Ljava/lang/String;)V
            part3 = part[1].split(';')
            #functionClass = self.makeClass(part3[0]+';')
            
            self.javaOp = javaOp('invoke')
            self.javaOp.addInput(params[0])
            self.javaOp.addInput(function)
            #for i in range(1,len(params)):
            #    self.javaOp.addInput(params[i])
            del params[0]
            for i in range(len(cs)):
                self.javaOp.addInput(cs[i])
                self.javaOp.addInput(params[i])                  
                
            self.javaOp.setType(retClass)
            self.javaMethod.addOp(self.javaOp)

        else:
            self.debug('<error> invoke :' + line)

    def nextReg(self, reg):
        n = int(reg[1:])
        n = n + 1
        ret = reg[0] + str(n)
        return ret
        
    def getValue(self, value, bit):
        if value[0] != "0" and value[0] != "-":
            return value
        if value[-1] == 'L':
            value = value[0:-1]
        ret = int(value, 16) >> (bit * 8)
        if ret < 0:
            ret = - ((-ret) & 0xFFFFFFFF)
        else:
            ret = ret & 0xFFFFFFFF
        #return hex(ret)[0:-1]
        return str(ret)
        
         

    def doConst(self, line, bit):
        # const/high16 v2, 0x7f03
        # const-string v2, ", "
        part = line.split(',', 1)
        part2 = part[0].split()
        var = part2[1]
        part[1] = part[1].strip()
        if bit == 0:
            if part[1][0] == '-':
                value = 0x10000 + int(part[1], 16)
                value = hex(value) + '0000'
            else:
                value = part[1].strip() + '0000'
            bit = 1
        else:
            value = part[1].strip()
        
        for i in range(bit):
            v = self.getValue(value, i)
            self.javaOp = javaOp('const')
            self.javaOp.setOutput(var)
            self.javaOp.addInput(v)
            self.javaOp.addInput(bit)
            self.javaMethod.addOp(self.javaOp)
            var = self.nextReg(var)

        

        
    def doPutGet(self, line, pg): # fix
        # iput-object v2, p0, Lcom/tutor/apkinstaller/ApkInstaller;->apkWeb:Landroid/webkit/WebView;  
        line = line.replace(', ', ',')
        part = line.split()
        part2 = part[1].split(',')
        field = self.makeField(part2[2])
        obj  = part2[1]
        value = part2[0]

        self.javaOp = javaOp(pg) # put/get
        #self.javaOp.setOutput(value)
        self.javaOp.addInput(obj)
        self.javaOp.addInput(field)
        if pg == 'put':
            self.javaOp.addInput(value)
        else:
            self.javaOp.setOutput(value)
        
        self.javaMethod.addOp(self.javaOp)

    def doStaticPutGet(self, line, pg): # fix
        # sput-object v1, Lcom/moji/mjweather/activity/AddCityActivity;->mHotCitys:[Ljava/lang/String;
        line = line.replace(', ', ' ')
        part = line.split()
        c = self.makeClass(part[2])
        field = self.makeField(part[2])  
        value = part[1]

        self.javaOp = javaOp(pg) # sput/sget
        #self.javaOp.setOutput(value)
        self.javaOp.addInput(c)
        self.javaOp.addInput(field)
        if pg == 'sput':
            self.javaOp.addInput(value)
        else:
            self.javaOp.setOutput(value)        
        self.javaMethod.addOp(self.javaOp)


    def doArrayPutGet(self, line, pg): # fix
        # aget-object v3, v3, v0
        line = line.replace(', ', ' ')
        part = line.split()
        
        value = part[1]
        obj = (part[2]) 
        aid = (part[3])  

        self.javaOp = javaOp(pg) # aput/aget
        #self.javaOp.setOutput(value)
        self.javaOp.addInput(obj)
        self.javaOp.addInput(aid)
        if pg == 'aput':
            self.javaOp.addInput(value)
        else:
            self.javaOp.setOutput(value)
        self.javaMethod.addOp(self.javaOp)

            
    def doMove(self, line):
        if line[4:11] == '-result':
        # move-result-object v2
            part = line.split()
            ret = part[1]
            
            self.javaOp.setOutput(ret)
            pass
        elif line[4:14] == '-exception':
        # move-exception v0
            part = line.split()
            ret = part[1]
            
            javaLabel = self.javaMethod.getLabel(self.curLabel)
            
            if javaLabel != None:
                javaLabel.setCatch(ret)
            else:
                print '<error exception>'
                print self.javaOp.op
#                self.javaOp = javaOp('move-exception')
#                self.javaOp.setOutput(ret)
#                self.javaOp.addInput('exception')
#                self.javaMethod.addOp(self.javaOp)
            pass
        else:
        # move-object/from16 v0, p0    
            line = line.replace(', ', ' ')
            part = line.split()
            var = part[1]
            value = part[2]
            self.javaOp = javaOp('move')
            self.javaOp.setOutput(var)
            self.javaOp.addInput(value)
            self.javaMethod.addOp(self.javaOp)
            if self.registers != None:
                self.registers[var] = value
            
            

            
    def doReturn(self, line):
        if line[6:11] == '-void':
            # return-void
            self.javaOp = javaOp('return')
            self.javaMethod.addOp(self.javaOp)
        else:
            part = line.split()
            if (len(part) > 1):
                ret = part[1]
                
                self.javaOp = javaOp('return')
                self.javaOp.addInput(ret)
                self.javaMethod.addOp(self.javaOp)
                
        if (self.javaLabel != None):
            self.javaLabel.setEnd(self.javaMethod.getOpCount())
            self.javaLabel = None
    
    def doGoto(self, line):
        part = line.split(':')
        label = part[1]
        
        if self.javaOp != None:
            self.javaOp.setLineEnd(True)
        
        self.javaOp = javaOp('goto')
        self.javaOp.addInput(label)
        self.javaMethod.addOp(self.javaOp)
        
        if (self.javaLabel != None):
            self.javaLabel.setEnd(self.javaMethod.getOpCount())
            self.javaLabel = None
    
    def doNew(self, line):
        line = line.replace(',', '')
        part = line.split()
        if line[3:12] == '-instance':
        # new-instance v1, Lcom/moji/mjweather/activity/AddCityActivity$1;
            var = part[1]
            c = self.makeClass(part[2])
            
            self.javaOp = javaOp('new')
            self.javaOp.setOutput(var)
            self.javaOp.addInput(c)
            self.javaMethod.addOp(self.javaOp)

            self.javaOps[var] = self.javaOp
            self.registers = {}
            
        elif line[3:9] == '-array':
        # new-array v1, v1, [Ljava/lang/String;
            var = part[1]
            size = (part[2])
            c= self.makeClass(part[3])
            
            self.javaOp = javaOp('anew')
            self.javaOp.setOutput(var)
            self.javaOp.addInput(c)
            self.javaOp.addInput(size)
            self.javaMethod.addOp(self.javaOp)            
    
    def doFillArray(self, line):
        # fill-array-data v0, :array_0
        line = line.replace(',', '')
        part = line.split()
        
        if self.javaOp != None and self.javaOp.op == 'anew':
            label = part[2][1:]
            self.javaOp.addInput(label)
        else:
            print '<error> fill array'
        
            
    
    def doIf(self, line):
        line = line.replace(',', '')
        part = line.split()
        if line[5] == 'z':
        # if-nez v1, :cond_0
            cal = part[0][3:5]
            c0 = (part[1])
            label = part[2][1:]
            
            self.javaOp = javaOp('ifz')
            self.javaOp.addInput(cal)
            self.javaOp.addInput(c0)
            self.javaOp.addInput(label)
            self.javaMethod.addOp(self.javaOp) 
        else:
        # if-ge v0, v1, :cond_1
            cal = part[0][3:5]
            c0 = (part[1])
            c1 = (part[2])
            label = part[3][1:]
        
            self.javaOp = javaOp('if')
            self.javaOp.addInput(cal)
            self.javaOp.addInput(c0)
            self.javaOp.addInput(c1)
            self.javaOp.addInput(label)
            self.javaMethod.addOp(self.javaOp) 
        
        

        
    def doCheck(self, line):
        # check-cast v1, Landroid/widget/ImageButton;
        line = line.replace(',', '')
        part = line.split()
        var = part[1]
        c = self.makeClass(part[2])

        self.javaOp = javaOp('check')
        self.javaOp.setOutput(var)
        self.javaOp.addInput(var)
        self.javaOp.addInput(c)
        self.javaMethod.addOp(self.javaOp)

    
    def doCalculate2(self, line): # fix
        # mul-double/2addr v3, v5
        line = line.replace(',', ' ')
        part = line.split()
        part2 = part[0].split('-')
        
        if (part[0].find('float') > 0):
            fpart = '-float'
        else:
            fpart = ''
        
        if part[0].find('2addr') > 0:
            ret = part[1]
            cal = part2[0]
            p1 = (part[1])
            p2 = (part[2])
            
            self.javaOp = javaOp('cal2' + fpart)
            self.javaOp.setOutput(ret)
            self.javaOp.addInput(cal)
            self.javaOp.addInput(p1)
            self.javaOp.addInput(p2)
            self.javaMethod.addOp(self.javaOp)            
            
        elif part[0].find('lit') > 0:
        #add-int/lit8 v9, v8, 0x1
            ret = part[1]
            cal = part2[0]
            p1 = (part[2])
            p2 = part[3]
            
            self.javaOp = javaOp('cal2-lit' + fpart)
            self.javaOp.setOutput(ret)
            self.javaOp.addInput(cal)
            self.javaOp.addInput(p1)
            self.javaOp.addInput(p2)
            self.javaMethod.addOp(self.javaOp)         
        else:
            ret = part[1]
            cal = part2[0]
            p1 = (part[2])
            p2 = (part[3])
        
            self.javaOp = javaOp('cal2' + fpart)
            self.javaOp.setOutput(ret)
            self.javaOp.addInput(cal)
            self.javaOp.addInput(p1)
            self.javaOp.addInput(p2)
            self.javaMethod.addOp(self.javaOp)           


    def doCalculate(self, line):
        # not-int vx, vy
        line = line.replace(',', ' ')
        part = line.split()
        part2 = part[0].split('-')
        
        var = part[1]
        value = (part[2])
        cal = part2[0]

        self.javaOp = javaOp('cal')
        self.javaOp.setOutput(var)
        self.javaOp.addInput(cal)
        self.javaOp.addInput(value)
        self.javaMethod.addOp(self.javaOp)  


    def doCmp(self, line):
        #cmpl-float v13, v11, v7
        line = line.replace(',', ' ')
        part = line.split()
        ret = part[1]
        value1 = (part[2])
        value2 = (part[3])

        self.javaOp = javaOp('cmp')
        self.javaOp.setOutput(ret)
        self.javaOp.addInput(value1)
        self.javaOp.addInput(value2)
        self.javaMethod.addOp(self.javaOp)  
        
        

    def doSwitch(self, line): # fix
        # sparse-switch v1, :sswitch_data_0
        # packed-switch p0, :pswitch_data_0
        line = line.replace(',', ' ')
        part = line.split()
        
        var = (part[1])
        data = part[2][1:]
        
        self.javaOp = javaOp('switch')
        self.javaOp.addInput(var)
        self.javaOp.addInput(data)
        self.javaMethod.addOp(self.javaOp)
    
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
        
        self.javaSwitch.addCase(value, label) 

    def doArray(self, line):
        # array-length v1, v1
        line = line.replace(',', ' ')
        part = line.split()
        ret = part[1]
        obj = (part[2])
        
        self.javaOp = javaOp('length')
        self.javaOp.setOutput(ret)
        self.javaOp.addInput(obj)
        self.javaMethod.addOp(self.javaOp)  

        
    
    def doTo(self, line):
        # int-to-double v3, v3
        line = line.replace(',', '')
        part = line.split()
        part2 = part[0].split('-to-')
        tdata = part[1]
        fdata = part[2]
        ttype = part2[1]
        
        self.javaOp = javaOp('to')
        self.javaOp.setOutput(tdata)
        self.javaOp.addInput(ttype)
        self.javaOp.addInput(fdata)
        self.javaMethod.addOp(self.javaOp)
    
    def doThrow(self, line):
        # throw v0
        part = line.split()
        value = (part[1])

        self.javaOp = javaOp('throw')
        self.javaOp.addInput(value)
        self.javaMethod.addOp(self.javaOp)

        if (self.javaLabel != None):
            self.javaLabel.setEnd(self.javaMethod.getOpCount())
            self.javaLabel = None
        
    def doInstanceOf(self, line):
        # instance-of v8, v7, Landroid/widget/TextView;
        line = line.replace(',', '')
        part = line.split()
        reg = part[1]
        value = (part[2])
        c = self.makeClass(part[3])
        
        self.javaOp = javaOp('instanceof')
        self.javaOp.setOutput(reg)
        self.javaOp.addInput(value)
        self.javaOp.addInput(c)
        self.javaMethod.addOp(self.javaOp)        


    def doMonitor(self, line):
        #monitor-enter p0
        part = line.split()
        obj = (part[1])

        self.javaOp = javaOp('monitor')
        self.javaMethod.addOp(self.javaOp)
        
        if line[7:13] == '-enter':
            pass
        elif line[7:12] == '-exit':
            pass
        else:
            self.debug('<error monitor> ' + line)


    def getAccess(self, name):
        if self.access.has_key(name):
            return self.access[name]
        return None

    def outputMethodOp(self, mid):
        method = self.javaClass.method[mid]
        if method.name[0:7] == 'access$':
            return
        
        #print '\tFunction Name: ' + method.name
        methodStaticOffset = 1
        string = ''
        if method.name != '<clinit>':
            for attr in method.attr:
                string = string + attr + ''
                if attr == 'static':
                    methodStaticOffset = 0

            string = method.retType + ' ' + method.name + '('
            
            if (methodStaticOffset == 1):
                method.reg.setRegister('p0', 'this', True)
            
            for i in range(len(method.paramType)):
                if (i < len(method.param)):
                    string = string + method.paramType[i] + ' ' + method.param[i]
                    method.reg.setRegister('p' + str(i + methodStaticOffset), method.param[i], True)
                else:
                    string = string + method.paramType[i] + ' ' + 'p' + str(i + methodStaticOffset)
                    method.reg.setRegister('p' + str(i + methodStaticOffset), 'p' + str(i + methodStaticOffset), True)
                    
                if (len(method.paramType) != i+1):
                    string = string + ','
            string = string + ')'
        else:
            string = string + 'static'
        string = string + '{'
        self.toFile(string)
        self.toFileShift(1)
        
        for local in method.local:
            string = local[0] + ' ' + local[1] + ';'
            self.toFile(string)
    
        for oid in range(len(method.op)):
            self.op2java(method, method.op, oid)
        self.toFileShift(-1)

        string = '}'
        self.toFile(string)
        self.toFile('')

    def toFileShift(self, shift):
        self.outputShift = self.outputShift + shift

    def toFile(self, string, shift = None):
        if shift == None:
            shift = self.outputShift
        for i in range(shift):
            string = '\t' + string

        self.outputFile.write(string + '\n')

    def opToShow(self, method, op, output, string, const = False):
        if (op.isLocal()):
            cvar = op.local[1]
            if cvar != string:
                string =  cvar + ' = ' + string + ';'
            else:
                string = ''
            method.reg.setRegister(op.output, cvar, True)            
        elif (op.isLineEnd()):
            string = output + ' = ' + string + ';'
            method.reg.setRegister(op.output, None)
        else:
            method.reg.setRegister(op.output, string, None, const)
            string = ''
        return string

    def opToShowDircet(self, method, op, output, string):
        if (op.isLocal()):
            cvar = op.local[1]
            string =  cvar + ' = ' + string + ';'
            method.reg.setRegister(op.output, cvar, True)            
        else:
            string = output + ' = ' + string + ';'
            method.reg.setRegister(op.output, None)
        return string
    
    def float2mbf4byte(self, f):
        ieee = struct.pack('f', f)
        sbin = [0] * 4;
        for i in range(4):
            sbin[i] = ord(ieee[i])
        return sbin
    
    
    def toFloat(self, strs):
        flag = ''
        if strs[0] == '-':
            return strs
            strs = strs[1:-1]
            flag = '-'
            
        
        if strs.isdigit():
            num = (int(strs))
            num = [(num & 0xFF) >> 0, (num & 0xFF00) >> 8, (num & 0xFF0000) >> 16, (num & 0xFF000000) >> 24]
            strs = ''.join(map(chr, num))
            #return format(struct.unpack('f', strs)[0], '.2f')
            #return '{0:f}'.format(struct.unpack('f', strs)[0])
            return str(struct.unpack('f', strs)[0])
        else:
            return flag + strs
    
    
    def op2java(self, method, ops, oid):
        op = ops[oid]
        
        inputs = method.reg.getRegisters(op.input)
        outputl = method.reg.getLocal(op.output)
        
        regs = op.getLocalEnd()
        for reg in regs:
            method.reg.setRegister(reg, None, False)          
        
        if op.label != None:
            mode = method.isTryLabel(op.label)
            if mode == None:
                if op.label[0:13] != 'sswitch_data_' and op.label[0:13] != 'pswitch_data_':
                    self.toFile(op.label + ':', 0)
                if op.label[0:5] == 'cond_':
                    method.reg.clearRegister()
            elif mode == True:
                self.toFile('try{')
                self.toFileShift(1)
            elif mode == False:
                tryCatch = method.getTryCatch(op.label)
                self.toFileShift(-1)
                self.toFile('}')
        if op.line != None and method.curLine != op.line:
            self.toFile('//line ' + op.line, 0)
            method.curLine = op.line
            
      
        
        string = None
        if op.op == 'catch':
            c = op.input[0]
            label = op.input[1]
            
            javaLabel = method.getLabel(label)
            
            if javaLabel.catch == None:
                var = 'exp'
            else:
                var = method.reg.getLocal(javaLabel.catch)

            self.toFile('catch ('+ c + ' ' + var + '){')
            self.toFileShift(1)
            self.toFile('goto ' + label + ';')
            self.toFileShift(-1)
            #self.toFile('}')
            string = '}'        
            pass
        elif op.op == 'sget':
            if self.javaClass.name != inputs[0]:
                string = inputs[0] + '.' + inputs[1]
            else:
                string = inputs[1]
            string = self.opToShow(method, op, outputl, string)
        elif op.op == 'sput':
            if self.javaClass.name != inputs[0]:
                string = inputs[0] + '.' + op.input[1] + ' = ' + inputs[2] + ';'
            else:
                string = op.input[1] + ' = ' + inputs[2] + ';'
        elif op.op == 'get':
            #if inputs[0] == 'this':
            #    string = inputs[0] + '->' + inputs[1]
            #else:
            string = inputs[0] + '.' + inputs[1]
            string = self.opToShow(method, op, outputl, string)
        elif op.op == 'put':
            #if inputs[0] == 'this':
            #    string = inputs[0] + '->' + op.input[1] + ' = ' + inputs[2] + ';'
            #else:
            string = inputs[0] + '.' + op.input[1] + ' = ' + inputs[2] + ';'
        elif op.op == 'const':
            string = inputs[0]
            string = self.opToShow(method, op, outputl, string, True)
        elif op.op == 'if':
            string = 'if (' + inputs[1] + ' ' + self.compare[op.input[0]] + ' ' + inputs[2] + ') ' + 'goto ' + op.input[3] + ';'
        elif op.op == 'new':
            string = ''
        elif op.op == 'new-invoke':
            string = 'new ' + op.input[0] + '('
            for i in range(2, len(inputs), 2):
                if inputs[i-1] == 'float':
                    p = self.toFloat(inputs[i])
                else:
                    p = inputs[i]
                if len(inputs) != i + 1 :
                    string = string + p + ', '
                else:
                    string = string + p
            string = string + ')'            
            string = self.opToShow(method, op, outputl, string)            
        elif op.op == 'return':
            string = 'return'
            if len(inputs) == 1:
                string = string + ' ' + inputs[0]
            string = string + ';'
        elif op.op == 'goto':
            string = 'goto ' + op.input[0] + ';'
        elif op.op == 'invoke':
            access = self.getAccess(op.input[1])
            #access = None
            if (access == None):
                string = inputs[0] + '.' + op.input[1] + '('
                for i in range(3, len(inputs),2):
                    if inputs[i-1] == 'float':
                        p = self.toFloat(inputs[i])
                    else:
                        p = inputs[i]
                    if len(op.input) != i + 1 :
                        string = string + p + ', '
                    else:
                        string = string + p
                string = string + ')'
                if op.output != None :
                    string = self.opToShow(method, op, outputl, string)
            else:
                if op.output != None:
                    string  = access
                    if op.output != None :
                        string = self.opToShow(method, op, outputl, string)                       
                else:
                    string = inputs[-1]
                    string = access + ' = ' + string
            if string != '':
                string = string + ';' 
                
        elif op.op == 'ifz':
            string = 'if (' + inputs[1] + ' ' + self.compare[op.input[0]] + ' ' + '0' + ') ' + 'goto ' + op.input[2] + ';'
        elif op.op == 'cal':
            string = self.calculate[op.input[0]] + inputs[1]
            string = self.opToShow(method, op, outputl, string)
            
        elif op.op[0:8] == 'cal2-lit':
            #print self.toFloat(inputs[0])
            flag = self.calculate[op.input[0]]
            #if (op.isLocal() and op.local[1] == outputl and inputs[2] == '0x1' and (flag == '+' or flag == '-')):
            if (op.isLocal() and op.local[1] == inputs[1] and (inputs[2] == '1' or inputs[2] == '0x1') and (flag == '+' or flag == '-')):
                string = inputs[1] + ' ' + flag + flag
                if not op.isLineEnd():
                    method.reg.setRegister(op.input[1], string)
                    method.reg.setRegister(op.output, op.local[1], True)
                    string = ''
            else:
                if op.op[9:14] == 'float':
                    p1 = self.toFloat(inputs[1])
                    p2 = self.toFloat(op.input[2])
                else:
                    p1 = (inputs[1])
                    p2 = (op.input[2]) 
                if p1[0] == '-':
                    p1 = '(' + p1 + ')'
                if p2[0] == '-':
                    p2 = '(' + p2 + ')'                
                string = p1 + ' ' + self.calculate[op.input[0]] + ' ' + p2
                string = self.opToShow(method, op, outputl, string)
        elif op.op[0:4] == 'cal2':
            if op.op[5:10] == 'float':
                p1 = self.toFloat(inputs[1])
                p2 = self.toFloat(inputs[2])
            else:
                p1 = (inputs[1])
                p2 = (inputs[2])                
            if p1[0] == '-':
                p1 = '(' + p1 + ')'
            if p2[0] == '-':
                p2 = '(' + p2 + ')'              
            string = p1 + ' ' + self.calculate[op.input[0]] + ' ' + p2
            string = self.opToShow(method, op, outputl, string)
        elif op.op == 'switch':
            string = 'swtich(' + inputs[0] + ')' + '{'
            self.toFile(string)
            string = 'goto ' + op.input[1]
            self.toFileShift(1)
            for case in method.switch[op.input[1]].case:
                string = 'case ' + case[0] + ': ' + 'goto ' + case[1] + ';'
                self.toFile(string)
            self.toFileShift(-1)
            string = '}' 
        elif op.op == 'move':
            string = inputs[0]
            string = self.opToShow(method, op, outputl, string)
        elif op.op == 'move-exception':
            string = inputs[0]
            method.reg.setRegister(op.output, string, None, False)
            string = ''            
        elif op.op == 'check':
            string = '(' + op.input[1] + ')' + inputs[0]
            string = self.opToShow(method, op, outputl, string)
        elif op.op == 'throw':
            string = 'throw ' + inputs[0] + ';'
        elif op.op == 'to':
            string = '(' + op.input[0] + ')' + inputs[1]
            string = self.opToShow(method, op, outputl, string)
        elif op.op == 'anew':
            c = op.input[0][0:-2] # int[] -> int
            string = 'new ' + c + '[' + inputs[1] + ']'
            string = self.opToShowDircet(method, op, outputl, string)
        elif op.op == 'instanceof':
            string = inputs[0] + ' instanceof ' + op.input[1]
            string = self.opToShow(method, op, outputl, string)
        elif op.op == 'aput':
            string =  inputs[0] + '[' + inputs[1] + '] = ' + inputs[2]
        elif op.op == 'aget':
            string = inputs[0] + '[' + inputs[1] + ']'
            string = self.opToShow(method, op, outputl, string)
        elif op.op == 'length':
            string = inputs[0] + '.length()'
            string = self.opToShow(method, op, outputl, string)
        elif op.op == 'cmp':
            string = '(' + inputs[0] + '>' + inputs[1] + '?1:' + inputs[0] + '<' + inputs[1] + '?-1:0)'
            string = self.opToShow(method, op, outputl, string)
        elif op.op == 'monitor':
            string = ''
        elif op.op == 'nop':
            if (op.isLocal()):
                cvar = op.local[1]
                #string =  cvar + ' = ' + string + ';'
                method.reg.setRegister(op.output, cvar, True) 
            string = ''


        

        
        if string == '':
            pass        
        elif string != None:
            self.toFile(string)
        else:
            print '<error show> ' + op.op
            
    def doParentTranslate(self, line):
        line = line.strip()
        
        if len(line)!=0:
            if (line[0] ==  '.'):
                self.doParentDot(line)
            elif (self.javaAccess != None):
                self.doParentCommand(line)    

    def doParentDot(self, line):
        if line[1:7] == 'method': # fix
            # .method public static main([Ljava/lang/String;)V
            part = line.split()
            part2 = part[-1].split('(')
            part3 = part2[1].split(')')

            functionName = part2[0]

            if (functionName[0:6] == 'access'):
                self.javaAccess = functionName
            
        elif line[1:11] == 'end method':
            self.access[self.javaAccess] = self.curAccess
            self.javaAccess = None

    def doParentCommand(self, line):
        if line[0:4] == 'iget':
            self.doParentPutGet(line)
        elif line[0:4] == 'sget':
            self.doParentStaticPutGet(line)

    def doParentPutGet(self, line): # fix
        # iput-object v2, p0, Lcom/tutor/apkinstaller/ApkInstaller;->apkWeb:Landroid/webkit/WebView;  
        line = line.replace(', ', ',')
        part = line.split()
        part2 = part[1].split(',')
        c = self.makeClass(part2[2])
        field = self.makeField(part2[2])
        self.curAccess = c + '.' + 'this.' + field

    def doParentStaticPutGet(self, line): # fix
        # sput-object v1, Lcom/moji/mjweather/activity/AddCityActivity;->mHotCitys:[Ljava/lang/String;
        line = line.replace(', ', ' ')
        part = line.split()
        c = self.makeClass(part[2])
        field = self.makeField(part[2])  
        self.curAccess = c + '.' + 'this.' + field


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

def getParent(file):
    path =  os.path.dirname(file)
    file =  os.path.basename(file)
    [file, ext] = os.path.splitext(file)
    
    ps = file.split('$')
    fps = []
    
    for i in range(len(ps)-1):
        p = ps[0]
        for ii in range(1,i+1):
            p = p + '$' + ps[ii]
        
        fp = os.path.join(path, p + ext)
        if (p != file and os.path.exists(fp)):
            fps.append(fp)
            
    return fps


def smaliToJava(smali, parents, java):
    fileSmali = open(smali)
    fileJava = open(java, 'w')
    
    sm = smali2java2()
    
    for parent in parents:
        fileParent = open(parent, 'r')
        for line in fileParent.readlines():
            sm.doParentTranslate(line)
        fileParent.close()
    
    for line in fileSmali.readlines():
#        try:
            sm.doTranslate(line)
#        except:
#            print line
#            print sys.exc_info()[0]
#            print sys.exc_info()[1]                        
#            fileSmali.close()
#            fileJava.close()
#            exit()

    sm.outputToFile(fileJava)
    fileSmali.close()
    fileJava.close()
    
if __name__ == "__main__":
    
    if len(sys.argv) == 3:
        dirs = sys.argv[1]
        dirj = sys.argv[2]
    elif len(sys.argv) == 2:
        dirs = sys.argv[1]
        dirj = dirs
    else:
        print 'smali2java [input dir] [output dir]'
        print 'version: 1.00'
        #exit()
        dirs = 'smali'
        dirj = 'smali'
        if (not os.path.exists(dirs)):
            exit()
        
    lists = listfile(dirs)
    
    for smali in lists:
        if smali[-6:] == '.smali':
            print 'FileName:' + smali
            java = smali.replace(dirs, dirj, 1)
            java = java.replace('.smali', '.java', -1)
            path = os.path.dirname(java)
            if not os.path.isdir(path):
                os.makedirs(path)
            parent = getParent(smali)
            
            smaliToJava(smali, parent, java)
            

import os
import struct
import sys


class JavaOp:
    def __init__(self, op):
        self.op = op
        self.output = None
        self.type = None
        self.input = []
        self.label = None
        self.line = None
        self.lineEnd = False
        self.local = None  # [reg, type, localName, restart]
        self.localEnd = []

    def set_output(self, output):
        self.output = output

    def set_type(self, op_type):
        self.type = op_type

    def add_input(self, op_input):
        self.input.append(op_input)

    def set_input(self, op_input):
        self.input = op_input

    def set_label(self, label):
        self.label = label

    def set_line(self, line):
        self.line = line

    def set_line_end(self, end):
        self.lineEnd = end

    def is_line_end(self):
        return self.lineEnd

    def set_local(self, cls, var, mode=None):
        self.local = [cls, var, mode]

    def is_local(self):
        if self.local is not None:
            return True
        return False

    def set_local_end(self, reg):
        self.localEnd.append(reg)

    def get_local_end(self):
        return self.localEnd


class JavaField:
    def __init__(self, name, f_type, value=None):
        self.name = name
        self.type = f_type
        self.attr = []
        self.value = value

    def add_attr(self, attr):
        self.attr.append(attr)


class JavaSwitch:
    def __init__(self):
        self.case = []

    def add_case(self, name, label):
        self.case.append([name, label])


class JavaLabel:
    def __init__(self, name):
        self.name = name
        self.catch = None

    def set_start(self, start):
        self.start = start

    def set_end(self, end):
        self.end = end

    def set_catch(self, catch):
        self.catch = catch


class JavaMethod:
    def __init__(self, name, ret_type=None):
        self.name = name
        self.attr = []
        self.ret_type = ret_type
        self.paramType = []
        self.param = []
        self.op = []
        self.label = {}
        self.switch = {}

        self.reg = JavaRegister()
        self.cur_line = None

        self.try_catch = []

        self.local = []

        pass

    def add_attr(self, attr):
        self.attr.append(attr)

    def add_param_type(self, param_type):
        self.paramType.append(param_type)

    def add_param(self, name):
        self.param.append(name)

    def add_op(self, op):
        self.op.append(op)

    def add_switch(self, name, data):
        self.switch[name] = data

    def add_label(self, name, data):
        self.label[name] = data

    def get_label(self, name):
        return self.label[name]

    def get_op_count(self):
        return len(self.op)

    def set_try_catch(self, label_start, label_end, exp_class, label_catch):
        self.try_catch.append([label_start, label_end, exp_class, label_catch])

    def get_try_catch(self, label_end):
        for tryCatch in self.try_catch:
            if tryCatch[1] == label_end:
                return tryCatch
        return None

    def is_try_label(self, label):
        for try_catch in self.try_catch:
            if try_catch[0] == label:
                return True
            if try_catch[1] == label:
                return False
        return None

    def add_local(self, c_type, var):
        for local in self.local:
            if local[1] == var:
                return
        self.local.append([c_type, var])


class JavaClass:
    def __init__(self, name):
        self.name = name
        self.super = None
        self.attr = []
        self.implement = []
        self.method = []
        self.field = []
        pass

    def set_super(self, name):
        self.super = name

    def add_attr(self, attr):
        self.attr.append(attr)

    def add_implement(self, name):
        self.implement.append(name)

    def add_field(self, name, f_type, value=None):
        field = JavaField(name, f_type, value)
        self.field.append(field)
        return field

    def add_method(self, method):
        self.method.append(method)


class JavaRegister:
    def __init__(self):
        self.register = {}
        self.local = {}
        self.const = {}

    def get_register(self, reg):
        if reg in self.register.keys() and self.register[reg] is not None:
            return self.register[reg]
        else:
            return reg

    def get_registers(self, regs):
        t_regs = []
        for reg in regs:
            t_regs.append(self.get_register(reg))
        return t_regs

    def set_register(self, reg, value, local=None, const=False):
        if not self.is_local(reg) or local is not None:
            self.register[reg] = value
            self.const[reg] = const

        if local:
            self.local[reg] = True
        elif not local:
            self.local[reg] = False

    def clear_register(self):
        for key in self.register.keys():
            if not (self.is_local(key) or self.is_const(key)):
                self.register[key] = key

    def get_local(self, reg):
        if reg is None:
            return None
        if self.is_local(reg):
            local = self.get_register(reg)
            return local
        return reg

    def is_local(self, reg):
        if reg not in self.local.keys():
            return False
        if not self.local[reg]:
            return False
        return True

    def is_const(self, reg):
        if reg not in self.const.keys():
            return False
        if not self.const[reg]:
            return False
        return True


class SmaliFile:
    def __init__(self, file_smali):
        self.file_smali = file_smali
        self.import_class = []
        self.switchBase = 0

        # V void - Z boolean B byte S short C char I int J long F float D double
        self.FLAG = {'V': 'void', 'Z': 'boolean', 'B': 'byte', 'S': 'short', 'C': 'char', 'I': 'int', 'J': 'long', 'F': 'float', 'D': 'double'}

        self.COMPARE = {'eq': '==', 'ne': '!=', 'lt': '<', 'ge': '>=', 'gt': '>', 'le': '<='}

        self.RE_COMPARE = {'eq': '!=', 'ne': '==', 'lt': '>=', 'ge': '<', 'gt': '<=', 'le': '>'}

        self.CALCULATE = {'add': '+', 'sub': '-', 'mul': '*', 'div': '/', 'rem': '%', 'and': '&', 'or': '|', 'xor': '^',
                          'shl': '<<', 'shr': '>>', 'ushr': '>>>', 'not': '!', 'neg': '-'}

        self.output_shift = 0

        self.annotation_mode = False
        self.array_data_mode = False

        self.java_op = None
        self.java_ops = None
        self.registers = None
        self.java_class = None
        self.java_method = None
        self.java_switch = None
        self.java_label = None

        self.cur_label = None
        self.cur_line = None

        self.line_info_enable = True
        self.local_info_enable = True

        self.access = {}
        self.java_access = None
        self.cur_access = None

        self.output_file = None

    @staticmethod
    def debug(msg):
        print(msg)
        pass

    def scan_file(self):
        fd_smali = open(self.file_smali)
        lines = fd_smali.readlines()
        fd_smali.close()

        for parent in self.get_parent_files(self.file_smali):
            fd_parent = open(parent, 'r')
            for line in fd_parent.readlines():
                self.do_parent_translate(line)
            fd_parent.close()

        for line in lines:
            try:
                self.do_translate(line)
            except: # ValueError, IndexError:
                print(line)
                print(sys.exc_info()[0])
                print(sys.exc_info()[1])
                exit()

    def to_java(self, file_java):
        fd_java = open(file_java, 'w')
        self.output_file = fd_java

        classes = set(self.import_class)

        file_string = ''
        for cls in classes:
            file_string = 'import ' + cls
            #            if cls != '':
            self.to_file(file_string)

            file_string = 'class '
        # for attr in self.JavaClass.attr:
        #    string = string + attr + ' '
        file_string = file_string + self.java_class.name
        if self.java_class.super is not None:
            file_string = file_string + ' extends ' + self.java_class.super
        if len(self.java_class.implement) != 0:
            file_string = file_string + ' implement '
            for i in range(len(self.java_class.implement)):
                if len(self.java_class.implement) == i + 1:
                    file_string = file_string + self.java_class.implement[i]
                else:
                    file_string = file_string + self.java_class.implement[i] + ', '
        self.to_file(file_string)

        file_string = '{'
        self.to_file(file_string)

        self.to_file_shift(1)

        for field in self.java_class.field:
            file_string = ''
            for attr in field.attr:
                file_string = file_string + attr + ' '
            file_string = file_string + field.type + ' ' + field.name
            if field.value is not None:
                file_string = file_string + ' = ' + field.value
            file_string = file_string + ';'

            self.to_file(file_string)

        for i in range(len(self.java_class.method)):
            self.output_method_op(i)
        self.to_file_shift(-1)

        file_string = '}'
        self.to_file(file_string)

        self.output_file = None
        fd_java.close()

    @staticmethod
    def get_parent_files(file_smali):
        path = os.path.dirname(file_smali)
        file = os.path.basename(file_smali)
        [file, ext] = os.path.splitext(file)

        ps = file.split('$')
        fps = []

        for i in range(len(ps) - 1):
            p = ps[0]
            for ii in range(1, i + 1):
                p = p + '$' + ps[ii]

            fp = os.path.join(path, p + ext)
            if p != file and os.path.exists(fp):
                fps.append(fp)

        return fps

    def append_method_to_file(self, string, line=None):
        pass

    def do_translate(self, line):
        line = line.strip()

        if len(line) != 0:
            if line.startswith('.'):
                self.do_dot(line)
            elif self.annotation_mode:
                pass
            elif self.array_data_mode:
                if self.java_label is None:
                    exit()
                pass
            elif self.java_switch is not None:
                self.do_switch_case(line)
            elif line.startswith(':'):
                self.do_label(line)
            elif line.startswith('#'):
                self.do_commit(line)
            else:
                self.do_command(line)

    def do_parent_translate(self, line):
        line = line.strip()

        if len(line) != 0:
            if line[0] == '.':
                self.do_parent_dot(line)
            elif self.java_access is not None:
                self.do_parent_command(line)

    def make_class(self, part, is_add=True):
        ret = '<error>'
        obj = False
        array = 0
        start = 0
        for i in range(len(part)):
            if not obj:
                if part[i] == '[':
                    array = array + 1
                elif part[i] == 'L':
                    obj = True
                    start = i
                else:
                    ret = self.FLAG[part[i]]
                    is_add = False
                    break
            else:
                if part[i] == ';':
                    cls = part[start + 1: i]
                    cls = cls.replace('/', '.')
                    ret = cls
                    break
        if is_add:
            self.import_class.append(ret)

        ret = ret.split('.')[-1]

        while array > 0:
            ret = (ret + '[]')
            array = array - 1

        return ret

    def make_function(self, part):
        # part : Landroid/app/Activity;->onCreate(Landroid/os/Bundle;)V
        start = part.find('>') + 1
        end = part.find('(')

        func = part[start:end]
        if func == '<init>':
            part2 = part.split(';')
            cls = self.make_class(part2[0] + ';')
            func = cls

        return func

    @staticmethod
    def make_params(part):
        # part : p0,p1
        # part : v0..v5
        if part.find('..') > 0:
            r_mode = True
        else:
            r_mode = False
        # part = part.replace('{', '')
        # part = part.replace('}', '')
        part = part.replace(',', ' ')
        part = part.replace('..', ' ')

        params = part.split()
        if not r_mode:
            if len(params) == 0 or params[0] == '':
                return []
            return params
        else:
            param2s = []
            vp = params[0][0]
            st = int(params[0][1:])
            end = int(params[1][1:]) + 1
            for i in range(st, end):
                param2s.append(vp + str(i))
            return param2s

    @staticmethod
    def make_field(part):
        # Lcom/tutor/apkinstaller/ApkInstaller;->apkWeb:Landroid/webkit/WebView;
        start = part.find('>') + 1
        end = part.find(':')
        return part[start:end]

    def make_params_class(self, part):
        cs = []
        obj = False
        array = 0
        start = 0
        for i in range(len(part)):
            if not obj:
                if part[i] == '[':
                    array = array + 1
                elif part[i] == 'L':
                    obj = True
                    start = i
                else:
                    cls = part[i - array:i + array + 1]
                    cls = self.make_class(cls)
                    cs.append(cls)
                    obj = False
                    array = 0
            else:
                if part[i] == ';':
                    cls = part[start - array:i + 1]
                    cls = self.make_class(cls)
                    cs.append(cls)
                    obj = False
                    array = 0
        return cs

    def do_dot(self, line):
        if line[1:5] == 'line':
            part = line.split()
            number = part[1]
            if self.cur_line is not None and self.java_op is not None:
                self.java_op.set_line_end(True)  # self.JavaOp = None
            self.cur_line = number

        elif line.startswith('class', 1):  # fix
            part = line.split()
            name = self.make_class(part[-1], False)
            self.java_class = JavaClass(name)

            for i in range(1, len(part) - 1):
                attr = part[i]
                self.java_class.add_attr(attr)

        elif line.startswith('super', 1):  # fix
            # .super Landroid/text/TextWatcher;
            part = line.split()
            name = self.make_class(part[-1])

            self.java_class.set_super(name)

        elif line.startswith('implements', 1):  # fix
            # .implements Landroid/text/TextWatcher;
            part = line.split()
            name = self.make_class(part[-1])
            self.java_class.add_implement(name)

        elif line.startswith('field', 1):  # fix
            # .field private static final COLUMN_INDEX_FIRST:I = 0x0
            part = line.split('=')

            part1 = part[0].strip().split()
            part2 = part1[-1].split(':')
            field = part2[0]
            field_class = self.make_class(part2[1])
            if len(part) == 2:
                value = part[1].strip()
            else:
                value = None

            v = self.java_class.add_field(field, field_class, value)

            for i in range(1, len(part1) - 1):
                attr = part1[i]
                v.add_attr(attr)  # self.JavaClass.add_attr(attr)

        elif line.startswith('end field', 1):  # fix
            pass
        elif line.startswith('method', 1):  # fix
            # .method public static main([Ljava/lang/String;)V
            part = line.split()
            part2 = part[-1].split('(')
            part3 = part2[1].split(')')
            if part2[0] != '<init>':
                func_name = part2[0]
            else:
                func_name = self.java_class.name
            fun_types = self.make_params_class(part3[0])
            fun_ret = self.make_class(part3[1])

            self.java_method = JavaMethod(func_name, fun_ret)
            self.java_class.add_method(self.java_method)

            for i in range(1, len(part) - 1):
                attr = part[i]
                self.java_method.add_attr(attr)

            for tpye in fun_types:
                self.java_method.add_param_type(tpye)

            self.java_op = None
            self.java_ops = {}
            self.registers = {}

        elif line[1:10] == 'parameter':
            # .parameter "x0"
            part = line.split()
            print(part)
            if len(part) > 1:
                para = part[1][1:-1]
                self.java_method.add_param(para)

        elif line[1:6] == 'param':
            # .param p0, "feedbackType"    # I   @baksmali
            line = line.replace(',', '')
            part = line.split()
            if len(part) > 2:
                para = part[2][1:-1]
                self.java_method.add_param(para)
        elif line.startswith('end param', 1):
            pass
        elif line.startswith('prologue', 1):  # fix
            pass
        elif line.startswith('end method', 1):  # fix
            self.java_method = None
            self.java_op = None
            self.java_ops = None
            self.registers = None
            self.cur_line = None
            self.cur_label = None

        elif line.startswith('locals', 1):
            pass
        elif line.startswith('local', 1) or line.startswith('restart local', 1):
            # .local v0, bundle:Landroid/os/Bundle;
            # .local v0, "bundle":Landroid/os/Bundle;   @ baksmali
            # .restart local v25    # "i":I              @ baksmli
            org_line = line
            line = line.replace(',', ' ')
            line = line.replace('#', ' ')
            line = line.replace('"', '')
            part = line.split()
            mode = False
            if line.startswith('restart', 1):
                del part[0]
            #                mode = True

            if len(part) > 2:
                part2 = part[2].split(':')
                var = part2[0]
                if var[0] == '#':
                    var = var[1:]
                reg = part[1]

                if len(part2) > 1:
                    part2[1] = part2[1].replace('"', '')
                    cls = self.make_class(part2[1])

                    if reg[0:2] != 'p0':
                        if self.java_op is not None and (
                                self.java_op.output == reg or self.java_method.reg.get_register(
                                self.java_op.output) == reg):
                            self.java_op.set_local(cls, var, mode)
                            self.java_method.add_local(cls, var)
                        else:
                            if self.java_label is not None and self.java_label.catch == reg:
                                self.java_label.catch = var

                            java_opl = JavaOp('nop')
                            java_opl.set_output(reg)
                            self.java_method.add_op(java_opl)
                            java_opl.set_local(cls, var, mode)
                            self.java_method.add_local(cls, var)
                else:
                    print('<error local>' + org_line)

        elif line.startswith('end local', 1):
            # .end local v0           #cityName:Ljava/lang/String;
            part = line.split()
            reg = part[2]

            self.java_op.set_local_end(reg)
            pass
        elif line.startswith('array-data', 1):
            self.array_data_mode = True
        elif line.startswith('end array-data', 1):
            self.array_data_mode = False
        elif line.startswith('annotation', 1):
            self.annotation_mode = True
        elif line.startswith('end annotation', 1):
            self.annotation_mode = False
            pass
        elif line.startswith('sparse-switch', 1) or line.startswith('packed-switch', 1):
            # .sparse-switch
            # .packed-switch 0x1
            part = line.split()
            if len(part) == 2:
                self.switchBase = int(part[1], 16)

            self.java_switch = JavaSwitch()
            self.java_method.add_switch(self.java_label.name, self.java_switch)

        elif line.startswith('end sparse-switch', 1) or line.startswith('end packed-switch', 1):
            self.java_switch = None
        elif line.startswith('catch', 1):
            # .catch Ljava/lang/Exception; {:try_start_7 .. :try_end_7} :catch_7
            part = line.split()
            if line.startswith('all', 6):
                cls = 'Exception'
            else:
                cls = self.make_class(part[1])
                del part[1]

            label_catch = part[4][1:]
            label_try_start = part[1][2:]
            label_try_end = part[3][1:-1]
            self.java_method.set_try_catch(label_try_start, label_try_end, cls, label_catch)

            java_opl = JavaOp('catch')
            java_opl.add_input(cls)
            java_opl.add_input(label_catch)
            self.java_method.add_op(java_opl)
        elif line.startswith('source', 1):
            pass

        elif line.startswith('registers', 1):
            pass
        else:
            self.debug('<error dot>' + line)

    def do_label(self, line):  # fix
        # :cond_1
        name = line[1:]

        self.cur_label = name
        self.java_label = JavaLabel(name)
        self.java_method.add_label(name, self.java_label)
        self.java_label.set_start(self.java_method.get_op_count())

        if self.cur_line is not None and self.java_op is not None:
            self.java_op.set_line_end(True)
        # self.JavaOp = None
        java_opl = JavaOp('nop')
        self.java_method.add_op(java_opl)
        java_opl.set_label(self.cur_label)

    def do_commit(self, line):
        # self.append_method_to_file('//' + line)
        pass

    def do_command(self, line):
        if line.startswith('invoke'):
            self.do_invoke(line)
        elif line.startswith('const'):
            if line[6:10] == 'wide':  # 64 bit
                self.do_const(line, 2)
            if line[6:12] == 'high16':
                self.do_const(line, 0)  # 16 bit
            else:
                self.do_const(line, 1)  # 32 bit
        elif line.startswith('iget'):
            self.do_put_get(line, 'get')
        elif line.startswith('iput'):
            self.do_put_get(line, 'put')
        elif line.startswith('sget'):
            self.do_static_put_get(line, 'sget')
        elif line.startswith('sput'):
            self.do_static_put_get(line, 'sput')
        elif line.startswith('aget'):
            self.do_array_put_get(line, 'aget')
        elif line.startswith('aput'):
            self.do_array_put_get(line, 'aput')
        elif line.startswith('move'):
            self.do_move(line)
        elif line.startswith('return'):
            self.do_return(line)
        elif line.startswith('goto'):
            self.do_goto(line)
        elif line.startswith('new'):
            self.do_new(line)
        elif line.startswith('fill-array-data'):
            self.do_fill_array(line)
        elif line.startswith('if'):
            self.do_if(line)
        elif line.startswith('check'):
            self.do_check(line)
        elif line.find('-to-') > 0:
            self.do_to(line)
        elif line.startswith('add') or line.startswith('sub') or line.startswith('mul') or line.startswith(
                'div') or line.startswith('rem') or line.startswith('and') or line.startswith('or') or line.startswith(
            'xor') or line.startswith('shl') or line.startswith('shr') or line.startswith('ushr'):
            self.do_calculate2(line)
        elif line.startswith('not') or line.startswith('neg'):
            self.do_calculate(line)
        elif line.startswith('cmp'):
            self.do_cmp(line)
        elif line.startswith('sparse-switch') or line.startswith('packed-switch'):
            self.do_switch(line)
            pass
        elif line.startswith('array-length'):
            self.do_array(line)
        elif line.startswith('throw'):
            self.do_throw(line)
        elif line.startswith('instance-of'):
            self.do_instance_of(line)
        elif line.startswith('nop'):
            self.java_op = JavaOp('nop')
            self.java_method.add_op(self.java_op)
        elif line.startswith('monitor'):
            self.do_monitor(line)
        else:
            # execute-inline
            # invoke-virtual/range {vx..vy},methodtocall
            # filled-new-array {parameters},type_id
            # const-class vx,type_id
            self.debug('<error> command:' + line)

        # if self.cur_label != None and self.JavaOp != None:
        #     self.JavaOp.set_label(self.cur_label)
        #     self.cur_label = None
        if self.java_op is not None and self.cur_line is not None:
            self.java_op.set_line(self.cur_line)  # self.cur_line = None

    def do_invoke(self, line):
        line = line.replace(', ', ',')
        line = line.replace(' .. ', '..')
        part = line.split('},')
        part2 = part[0].split()
        func = self.make_function(part[1])
        params = self.make_params(part2[1][1:])
        cs = self.make_params_class(part[1].split('(')[1].split(')')[0])
        # print cs

        s = 0
        if not line.startswith('-static', 6):
            s = 1

        for i in range(len(cs)):
            if cs[i] == 'double' or cs[i] == 'long':
                del params[i + 1 + s]
        # print params

        ret_class = line.split(')')[-1]

        if ret_class != 'V':
            pass

        if line.startswith('-super', 6):  # fix
            # invoke-super {p0, p1}, Landroid/app/Activity;->onCreate(Landroid/os/Bundle;)V
            self.java_op = JavaOp('invoke')
            self.java_op.add_input('super')
            self.java_op.add_input(func)
            del params[0]
            # for param in params:
            #     self.JavaOp.add_input(param)
            for i in range(len(cs)):
                self.java_op.add_input(cs[i])
                self.java_op.add_input(params[i])

            self.java_op.set_type(ret_class)
            self.java_method.add_op(self.java_op)

        elif line.startswith('-direct', 6):  # fix
            # invoke-direct {v0}, Ljava/lang/RuntimeException;-><init>()V
            for i in range(len(params)):
                if self.registers is not None and params[i] in self.registers.keys():
                    params[i] = self.registers[params[i]]
            self.registers = None

            obj = params[0]

            if obj in self.java_ops.keys():
                self.java_op = JavaOp('new-invoke')
                self.java_op.set_output(self.java_ops[obj].output)
                self.java_op.set_input(self.java_ops[obj].input)
                # self.JavaOp = self.JavaOps[obj]
                # for i in range(1,len(params)):
                #     self.JavaOp.add_input(params[i])
                del params[0]
                for i in range(len(cs)):
                    self.java_op.add_input(cs[i])
                    self.java_op.add_input(params[i])
                self.java_method.add_op(self.java_op)
                del self.java_ops[obj]
            else:
                self.java_op = JavaOp('invoke')
                self.java_op.add_input(params[0])
                self.java_op.add_input(func)
                # for i in range(1,len(params)):
                #    self.JavaOp.add_input(params[i])
                del params[0]
                for i in range(len(cs)):
                    self.java_op.add_input(cs[i])
                    self.java_op.add_input(params[i])
                self.java_op.set_type(ret_class)
                self.java_method.add_op(self.java_op)

        elif line.startswith('-static', 6):
            # invoke-static {p1}, Landroid/text/TextUtils;->isEmpty(Ljava/lang/CharSequence;)Z
            part3 = part[1].split(';')
            func_class = self.make_class(part3[0] + ';')

            self.java_op = JavaOp('invoke')
            self.java_op.add_input(func_class)
            self.java_op.add_input(func)
            # for param in params:
            #     self.JavaOp.add_input(param)
            for i in range(len(cs)):
                self.java_op.add_input(cs[i])
                self.java_op.add_input(params[i])
            self.java_op.set_type(ret_class)
            self.java_method.add_op(self.java_op)

        elif line.startswith('-virtual', 6) or line.startswith('-interface', 6):
            # invoke-virtual {v2, v0}, Landroid/webkit/WebView;->loadUrl(Ljava/lang/String;)V
            # func_class = self.make_class(part3[0]+';')

            self.java_op = JavaOp('invoke')
            self.java_op.add_input(params[0])
            self.java_op.add_input(func)
            # for i in range(1,len(params)):
            #     self.JavaOp.add_input(params[i])
            del params[0]
            for i in range(len(cs)):
                self.java_op.add_input(cs[i])
                self.java_op.add_input(params[i])

            self.java_op.set_type(ret_class)
            self.java_method.add_op(self.java_op)

        else:
            self.debug('<error> invoke :' + line)

    @staticmethod
    def next_reg(reg):
        n = int(reg[1:])
        n = n + 1
        ret = reg[0] + str(n)
        return ret

    @staticmethod
    def get_value(value, bit):
        if value[0] != "0" and value[0] != "-":
            return value
        if value[-1] == 'L':
            value = value[0:-1]
        ret = int(value, 16) >> (bit * 8)
        if ret < 0:
            ret = - ((-ret) & 0xFFFFFFFF)
        else:
            ret = ret & 0xFFFFFFFF
        # return hex(ret)[0:-1]
        return str(ret)

    def do_const(self, line, bit):
        # const/high16 v2, 0x7f03
        # const/high16 p0, 0x3f800000    # 1.0f
        # const-string v2, ", "
        part = line.split(',', 1)
        part2 = part[0].split()
        var = part2[1]
        part[1] = part[1].split('#')[0]
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
            v = self.get_value(value, i)
            self.java_op = JavaOp('const')
            self.java_op.set_output(var)
            self.java_op.add_input(v)
            self.java_op.add_input(bit)
            self.java_method.add_op(self.java_op)
            var = self.next_reg(var)

    def do_put_get(self, line, pg):  # fix
        # iput-object v2, p0, Lcom/tutor/apkinstaller/ApkInstaller;->apkWeb:Landroid/webkit/WebView;
        line = line.replace(', ', ',')
        part = line.split()
        part2 = part[1].split(',')
        field = self.make_field(part2[2])
        obj = part2[1]
        value = part2[0]

        self.java_op = JavaOp(pg)  # put/get
        # self.JavaOp.set_output(value)
        self.java_op.add_input(obj)
        self.java_op.add_input(field)
        if pg == 'put':
            self.java_op.add_input(value)
        else:
            self.java_op.set_output(value)

        self.java_method.add_op(self.java_op)

    def do_static_put_get(self, line, pg):  # fix
        # sput-object v1, Lcom/moji/mjweather/activity/AddCityActivity;->mHotCitys:[Ljava/lang/String;
        line = line.replace(', ', ' ')
        part = line.split()
        cls = self.make_class(part[2])
        field = self.make_field(part[2])
        value = part[1]

        self.java_op = JavaOp(pg)  # sput/sget
        # self.JavaOp.set_output(value)
        self.java_op.add_input(cls)
        self.java_op.add_input(field)
        if pg == 'sput':
            self.java_op.add_input(value)
        else:
            self.java_op.set_output(value)
        self.java_method.add_op(self.java_op)

    def do_array_put_get(self, line, pg):  # fix
        # aget-object v3, v3, v0
        line = line.replace(', ', ' ')
        part = line.split()

        value = part[1]
        obj = (part[2])
        aid = (part[3])

        self.java_op = JavaOp(pg)  # aput/aget
        # self.JavaOp.set_output(value)
        self.java_op.add_input(obj)
        self.java_op.add_input(aid)
        if pg == 'aput':
            self.java_op.add_input(value)
        else:
            self.java_op.set_output(value)
        self.java_method.add_op(self.java_op)

    def do_move(self, line):
        if line.startswith('-result', 4):
            # move-result-object v2
            part = line.split()
            ret = part[1]

            self.java_op.set_output(ret)
            pass
        elif line.startswith('-exception', 4):
            # move-exception v0
            part = line.split()
            ret = part[1]

            java_label = self.java_method.get_label(self.cur_label)

            if java_label is not None:
                java_label.set_catch(ret)
            else:
                print('<error exception>')
                print(self.java_op.op)
            #                self.JavaOp = JavaOp('move-exception')
            #                self.JavaOp.set_output(ret)
            #                self.JavaOp.add_input('exception')
            #                self.JavaMethod.add_op(self.JavaOp)
            pass
        else:
            # move-object/from16 v0, p0
            line = line.replace(', ', ' ')
            part = line.split()
            var = part[1]
            value = part[2]
            self.java_op = JavaOp('move')
            self.java_op.set_output(var)
            self.java_op.add_input(value)
            self.java_method.add_op(self.java_op)
            if self.registers is not None:
                self.registers[var] = value

    def do_return(self, line):
        if line.startswith('-void', 6):
            # return-void
            self.java_op = JavaOp('return')
            self.java_method.add_op(self.java_op)
        else:
            part = line.split()
            if len(part) > 1:
                ret = part[1]

                self.java_op = JavaOp('return')
                self.java_op.add_input(ret)
                self.java_method.add_op(self.java_op)

        if self.java_label is not None:
            self.java_label.set_end(self.java_method.get_op_count())
            self.java_label = None

    def do_goto(self, line):
        part = line.split(':')
        label = part[1]

        if self.java_op is not None:
            self.java_op.set_line_end(True)

        self.java_op = JavaOp('goto')
        self.java_op.add_input(label)
        self.java_method.add_op(self.java_op)

        if self.java_label is not None:
            self.java_label.set_end(self.java_method.get_op_count())
            self.java_label = None

    def do_new(self, line):
        line = line.replace(',', '')
        part = line.split()
        if line.startswith('-instance', 3):
            # new-instance v1, Lcom/moji/mjweather/activity/AddCityActivity$1;
            var = part[1]
            cls = self.make_class(part[2])

            self.java_op = JavaOp('new')
            self.java_op.set_output(var)
            self.java_op.add_input(cls)
            self.java_method.add_op(self.java_op)

            self.java_ops[var] = self.java_op
            self.registers = {}

        elif line.startswith('-array', 3):
            # new-array v1, v1, [Ljava/lang/String;
            var = part[1]
            size = (part[2])
            cls = self.make_class(part[3])

            self.java_op = JavaOp('anew')
            self.java_op.set_output(var)
            self.java_op.add_input(cls)
            self.java_op.add_input(size)
            self.java_method.add_op(self.java_op)

    def do_fill_array(self, line):
        # fill-array-data v0, :array_0
        line = line.replace(',', '')
        part = line.split()

        if self.java_op is not None and self.java_op.op == 'anew':
            label = part[2][1:]
            self.java_op.add_input(label)
        else:
            print('<error> fill array')

    def do_if(self, line):
        line = line.replace(',', '')
        part = line.split()
        if line.startswith('z', 5):
            # if-nez v1, :cond_0
            cal = part[0][3:5]
            c0 = (part[1])
            label = part[2][1:]

            self.java_op = JavaOp('ifz')
            self.java_op.add_input(cal)
            self.java_op.add_input(c0)
            self.java_op.add_input(label)
            self.java_method.add_op(self.java_op)
        else:
            # if-ge v0, v1, :cond_1
            cal = part[0][3:5]
            c0 = (part[1])
            c1 = (part[2])
            label = part[3][1:]

            self.java_op = JavaOp('if')
            self.java_op.add_input(cal)
            self.java_op.add_input(c0)
            self.java_op.add_input(c1)
            self.java_op.add_input(label)
            self.java_method.add_op(self.java_op)

    def do_check(self, line):
        # check-cast v1, Landroid/widget/ImageButton;
        line = line.replace(',', '')
        part = line.split()
        var = part[1]
        cls = self.make_class(part[2])

        self.java_op = JavaOp('check')
        self.java_op.set_output(var)
        self.java_op.add_input(var)
        self.java_op.add_input(cls)
        self.java_method.add_op(self.java_op)

    def do_calculate2(self, line):  # fix
        # mul-double/2addr v3, v5
        line = line.replace(',', ' ')
        part = line.split()
        part2 = part[0].split('-')

        if part[0].find('float') > 0:
            fpart = '-float'
        else:
            fpart = ''

        if part[0].find('2addr') > 0:
            ret = part[1]
            cal = part2[0]
            p1 = part[1]
            p2 = part[2]

            self.java_op = JavaOp('cal2' + fpart)
            self.java_op.set_output(ret)
            self.java_op.add_input(cal)
            self.java_op.add_input(p1)
            self.java_op.add_input(p2)
            self.java_method.add_op(self.java_op)

        elif part[0].find('lit') > 0:
            # add-int/lit8 v9, v8, 0x1
            ret = part[1]
            cal = part2[0]
            p1 = (part[2])
            p2 = part[3]

            self.java_op = JavaOp('cal2-lit' + fpart)
            self.java_op.set_output(ret)
            self.java_op.add_input(cal)
            self.java_op.add_input(p1)
            self.java_op.add_input(p2)
            self.java_method.add_op(self.java_op)
        else:
            ret = part[1]
            cal = part2[0]
            p1 = (part[2])
            p2 = (part[3])

            self.java_op = JavaOp('cal2' + fpart)
            self.java_op.set_output(ret)
            self.java_op.add_input(cal)
            self.java_op.add_input(p1)
            self.java_op.add_input(p2)
            self.java_method.add_op(self.java_op)

    def do_calculate(self, line):
        # not-int vx, vy
        line = line.replace(',', ' ')
        part = line.split()
        part2 = part[0].split('-')

        var = part[1]
        value = (part[2])
        cal = part2[0]

        self.java_op = JavaOp('cal')
        self.java_op.set_output(var)
        self.java_op.add_input(cal)
        self.java_op.add_input(value)
        self.java_method.add_op(self.java_op)

    def do_cmp(self, line):
        # cmpl-float v13, v11, v7
        line = line.replace(',', ' ')
        part = line.split()
        ret = part[1]
        value1 = (part[2])
        value2 = (part[3])

        self.java_op = JavaOp('cmp')
        self.java_op.set_output(ret)
        self.java_op.add_input(value1)
        self.java_op.add_input(value2)
        self.java_method.add_op(self.java_op)

    def do_switch(self, line):  # fix
        # sparse-switch v1, :sswitch_data_0
        # packed-switch p0, :pswitch_data_0
        line = line.replace(',', ' ')
        part = line.split()

        var = (part[1])
        data = part[2][1:]

        self.java_op = JavaOp('switch')
        self.java_op.add_input(var)
        self.java_op.add_input(data)
        self.java_method.add_op(self.java_op)

    def do_switch_case(self, line):
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

        self.java_switch.add_case(value, label)

    def do_array(self, line):
        # array-length v1, v1
        line = line.replace(',', ' ')
        part = line.split()
        ret = part[1]
        obj = (part[2])

        self.java_op = JavaOp('length')
        self.java_op.set_output(ret)
        self.java_op.add_input(obj)
        self.java_method.add_op(self.java_op)

    def do_to(self, line):
        # int-to-double v3, v3
        line = line.replace(',', '')
        part = line.split()
        part2 = part[0].split('-to-')
        t_data = part[1]
        f_data = part[2]
        t_type = part2[1]

        self.java_op = JavaOp('to')
        self.java_op.set_output(t_data)
        self.java_op.add_input(t_type)
        self.java_op.add_input(f_data)
        self.java_method.add_op(self.java_op)

    def do_throw(self, line):
        # throw v0
        part = line.split()
        value = (part[1])

        self.java_op = JavaOp('throw')
        self.java_op.add_input(value)
        self.java_method.add_op(self.java_op)

        if self.java_label is not None:
            self.java_label.set_end(self.java_method.get_op_count())
            self.java_label = None

    def do_instance_of(self, line):
        # instance-of v8, v7, Landroid/widget/TextView;
        line = line.replace(',', '')
        part = line.split()
        reg = part[1]
        value = (part[2])
        cls = self.make_class(part[3])

        self.java_op = JavaOp('instanceof')
        self.java_op.set_output(reg)
        self.java_op.add_input(value)
        self.java_op.add_input(cls)
        self.java_method.add_op(self.java_op)

    def do_monitor(self, line):
        # monitor-enter p0
        self.java_op = JavaOp('monitor')
        self.java_method.add_op(self.java_op)

        if line.startswith('-enter', 7):
            pass
        elif line.startswith('-exit', 7):
            pass
        else:
            self.debug('<error monitor> ' + line)

    def get_access(self, name):
        if name in self.access.keys():
            return self.access[name]
        return None

    def output_method_op(self, mid):
        method = self.java_class.method[mid]
        if method.name.startswith('access$'):
            return

        # print '\tFunction Name: ' + method.name
        method_static_offset = 1
        string = ''
        if method.name != '<clinit>':
            for attr in method.attr:
                string = string + attr + ''
                if attr == 'static':
                    method_static_offset = 0

            string = method.ret_type + ' ' + method.name + '('

            if method_static_offset == 1:
                method.reg.set_register('p0', 'this', True)

            for i in range(len(method.paramType)):
                if i < len(method.param):
                    string = string + method.paramType[i] + ' ' + method.param[i]
                    method.reg.set_register('p' + str(i + method_static_offset), method.param[i], True)
                else:
                    string = string + method.paramType[i] + ' ' + 'p' + str(i + method_static_offset)
                    method.reg.set_register('p' + str(i + method_static_offset), 'p' + str(i + method_static_offset),
                                            True)

                if len(method.paramType) != i + 1:
                    string = string + ','
            string = string + ')'
        else:
            string = string + 'static'
        string = string + '{'
        self.to_file(string)
        self.to_file_shift(1)

        for local in method.local:
            string = local[0] + ' ' + local[1] + ';'
            self.to_file(string)

        for oid in range(len(method.op)):
            self.op2java(method, method.op, oid)
        self.to_file_shift(-1)

        string = '}'
        self.to_file(string)
        self.to_file('')

    def to_file_shift(self, shift):
        self.output_shift = self.output_shift + shift

    def to_file(self, string, shift=None):
        if shift is None:
            shift = self.output_shift
        for i in range(shift):
            string = '\t' + string

        self.output_file.write(string + '\n')

    @staticmethod
    def op_to_show(method, op, output, string, const=False):
        if op.is_local():
            c_var = op.local[1]
            if c_var != string:
                string = c_var + ' = ' + string + ';'
            else:
                string = ''
            method.reg.set_register(op.output, c_var, True)
        elif op.is_line_end():
            string = output + ' = ' + string + ';'
            method.reg.set_register(op.output, None)
        else:
            method.reg.set_register(op.output, string, None, const)
            string = ''
        return string

    @staticmethod
    def op_to_show_dircet(method, op, output, string):
        if op.is_local():
            cvar = op.local[1]
            string = cvar + ' = ' + string + ';'
            method.reg.set_register(op.output, cvar, True)
        else:
            string = output + ' = ' + string + ';'
            method.reg.set_register(op.output, None)
        return string

    @staticmethod
    def float2mbf4byte(f):
        p_ieee = struct.pack('f', f)
        sbin = [0] * 4
        for i in range(4):
            sbin[i] = ord(p_ieee[i])
        return sbin

    @staticmethod
    def to_float(f_str):
        flag = ''
        if f_str.startswith('-'):
            return f_str

        if f_str.isdigit():
            num = (int(f_str))
            f_str = num.to_bytes(length=4, byteorder='big')

            return str(struct.unpack('f', f_str)[0])
        else:
            return flag + f_str

    def op2java(self, method, ops, oid):
        op = ops[oid]

        inputs = method.reg.get_registers(op.input)
        output_l = method.reg.get_local(op.output)

        regs = op.get_local_end()
        for reg in regs:
            method.reg.set_register(reg, None, False)

        if op.label is not None:
            mode = method.is_try_label(op.label)
            if mode is None:
                if not op.label.startswith('sswitch_data_') and not op.label.startswith('pswitch_data_'):
                    self.to_file(op.label + ':', 0)
                if op.label.startswith('cond_'):
                    method.reg.clear_register()
            elif mode:
                self.to_file('try{')
                self.to_file_shift(1)
            elif not mode:
                self.to_file_shift(-1)
                self.to_file('}')
        if op.line is not None and method.cur_line != op.line:
            self.to_file('//line ' + op.line, 0)
            method.cur_line = op.line

        op_string = None
        if op.op == 'catch':
            cls = op.input[0]
            label = op.input[1]

            java_label = method.get_label(label)

            if java_label.catch is None:
                var = 'exp'
            else:
                var = method.reg.get_local(java_label.catch)

            self.to_file('catch (' + cls + ' ' + var + '){')
            self.to_file_shift(1)
            self.to_file('goto ' + label + ';')
            self.to_file_shift(-1)
            # self.to_file('}')
            op_string = '}'
            pass
        elif op.op == 'sget':
            if self.java_class.name != inputs[0]:
                op_string = inputs[0] + '.' + inputs[1]
            else:
                op_string = inputs[1]
            op_string = self.op_to_show(method, op, output_l, op_string)
        elif op.op == 'sput':
            if self.java_class.name != inputs[0]:
                op_string = inputs[0] + '.' + op.input[1] + ' = ' + inputs[2] + ';'
            else:
                op_string = op.input[1] + ' = ' + inputs[2] + ';'
        elif op.op == 'get':
            # if inputs[0] == 'this':
            #     op_string = inputs[0] + '->' + inputs[1]
            # else:
            op_string = inputs[0] + '.' + inputs[1]
            op_string = self.op_to_show(method, op, output_l, op_string)
        elif op.op == 'put':
            # if inputs[0] == 'this':
            #     op_string = inputs[0] + '->' + op.input[1] + ' = ' + inputs[2] + ';'
            # else:
            op_string = inputs[0] + '.' + op.input[1] + ' = ' + inputs[2] + ';'
        elif op.op == 'const':
            op_string = inputs[0]
            op_string = self.op_to_show(method, op, output_l, op_string, True)
        elif op.op == 'if':
            op_string = 'if (' + inputs[1] + ' ' + self.COMPARE[op.input[0]] + ' ' + inputs[2] + ') ' + 'goto ' + \
                        op.input[3] + ';'
        elif op.op == 'new':
            op_string = ''
        elif op.op == 'new-invoke':
            op_string = 'new ' + op.input[0] + '('
            for i in range(2, len(inputs), 2):
                if inputs[i - 1] == 'float':
                    p = self.to_float(inputs[i])
                else:
                    p = inputs[i]
                if len(inputs) != i + 1:
                    op_string = op_string + p + ', '
                else:
                    op_string = op_string + p
            op_string = op_string + ')'
            op_string = self.op_to_show(method, op, output_l, op_string)
        elif op.op == 'return':
            op_string = 'return'
            if len(inputs) == 1:
                op_string = op_string + ' ' + inputs[0]
            op_string = op_string + ';'
        elif op.op == 'goto':
            op_string = 'goto ' + op.input[0] + ';'
        elif op.op == 'invoke':
            access = self.get_access(op.input[1])
            # access = None
            if access is None:
                op_string = inputs[0] + '.' + op.input[1] + '('
                for i in range(3, len(inputs), 2):
                    if inputs[i - 1] == 'float':
                        p = self.to_float(inputs[i])
                    else:
                        p = inputs[i]
                    if len(op.input) != i + 1:
                        op_string = op_string + p + ', '
                    else:
                        op_string = op_string + p
                op_string = op_string + ')'
                if op.output is not None:
                    op_string = self.op_to_show(method, op, output_l, op_string)
            else:
                if op.output is not None:
                    op_string = access
                    if op.output is not None:
                        op_string = self.op_to_show(method, op, output_l, op_string)
                else:
                    op_string = inputs[-1]
                    op_string = access + ' = ' + op_string
            if op_string != '':
                op_string = op_string + ';'

        elif op.op == 'ifz':
            op_string = 'if (' + inputs[1] + ' ' + self.COMPARE[op.input[0]] + ' ' + '0' + ') ' + 'goto ' + op.input[
                2] + ';'
        elif op.op == 'cal':
            op_string = self.CALCULATE[op.input[0]] + inputs[1]
            op_string = self.op_to_show(method, op, output_l, op_string)

        elif op.op.startswith('cal2-lit'):
            # print self.to_float(inputs[0])
            flag = self.CALCULATE[op.input[0]]
            # if (op.is_local() and op.local[1] == output_l and inputs[2] == '0x1' and (flag == '+' or flag == '-')):
            if (op.is_local() and op.local[1] == inputs[1] and (inputs[2] == '1' or inputs[2] == '0x1') and (
                    flag == '+' or flag == '-')):
                op_string = inputs[1] + ' ' + flag + flag
                if not op.is_line_end():
                    method.reg.set_register(op.input[1], op_string)
                    method.reg.set_register(op.output, op.local[1], True)
                    op_string = ''
            else:
                if op.op[9:].startswith('float'):
                    p1 = self.to_float(inputs[1])
                    p2 = self.to_float(op.input[2])
                else:
                    p1 = (inputs[1])
                    p2 = (op.input[2])
                if p1.startswith('-'):
                    p1 = '(' + p1 + ')'
                if p2.startswith('-'):
                    p2 = '(' + p2 + ')'
                op_string = p1 + ' ' + self.CALCULATE[op.input[0]] + ' ' + p2
                op_string = self.op_to_show(method, op, output_l, op_string)
        elif op.op.startswith('cal2'):
            if op.op[5:10] == 'float':
                p1 = self.to_float(inputs[1])
                p2 = self.to_float(inputs[2])
            else:
                p1 = (inputs[1])
                p2 = (inputs[2])

            if len(p1) == 0:
                print(op.input[0])
                print(inputs[1])
                print(inputs[2])

            if p1.startswith('-'):
                p1 = '(' + p1 + ')'
            if p2.startswith('-'):
                p2 = '(' + p2 + ')'
            op_string = p1 + ' ' + self.CALCULATE[op.input[0]] + ' ' + p2
            op_string = self.op_to_show(method, op, output_l, op_string)
        elif op.op == 'switch':
            op_string = 'swtich(' + inputs[0] + ')' + '{'
            self.to_file(op_string)
            self.to_file_shift(1)
            for case in method.switch[op.input[1]].case:
                op_string = 'case ' + case[0] + ': ' + 'goto ' + case[1] + ';'
                self.to_file(op_string)
            self.to_file_shift(-1)
            op_string = '}'
        elif op.op == 'move':
            op_string = inputs[0]
            op_string = self.op_to_show(method, op, output_l, op_string)
        elif op.op == 'move-exception':
            op_string = inputs[0]
            method.reg.set_register(op.output, op_string, None, False)
            op_string = ''
        elif op.op == 'check':
            op_string = '(' + op.input[1] + ')' + inputs[0]
            op_string = self.op_to_show(method, op, output_l, op_string)
        elif op.op == 'throw':
            op_string = 'throw ' + inputs[0] + ';'
        elif op.op == 'to':
            op_string = '(' + op.input[0] + ')' + inputs[1]
            op_string = self.op_to_show(method, op, output_l, op_string)
        elif op.op == 'anew':
            cls = op.input[0][0:-2]  # int[] -> int
            op_string = 'new ' + cls + '[' + inputs[1] + ']'
            op_string = self.op_to_show_dircet(method, op, output_l, op_string)
        elif op.op == 'instanceof':
            op_string = inputs[0] + ' instanceof ' + op.input[1]
            op_string = self.op_to_show(method, op, output_l, op_string)
        elif op.op == 'aput':
            op_string = inputs[0] + '[' + inputs[1] + '] = ' + inputs[2]
        elif op.op == 'aget':
            op_string = inputs[0] + '[' + inputs[1] + ']'
            op_string = self.op_to_show(method, op, output_l, op_string)
        elif op.op == 'length':
            op_string = inputs[0] + '.length()'
            op_string = self.op_to_show(method, op, output_l, op_string)
        elif op.op == 'cmp':
            op_string = '(' + inputs[0] + '>' + inputs[1] + '?1:' + inputs[0] + '<' + inputs[1] + '?-1:0)'
            op_string = self.op_to_show(method, op, output_l, op_string)
        elif op.op == 'monitor':
            op_string = ''
        elif op.op == 'nop':
            if op.is_local():
                c_var = op.local[1]
                method.reg.set_register(op.output, c_var, True)
            op_string = ''

        if op_string == '':
            pass
        elif op_string is not None:
            self.to_file(op_string)
        else:
            print('<error show> ' + op.op)

    def do_parent_dot(self, line):
        if line.startswith('method', 1):  # fix
            # .method public static main([Ljava/lang/String;)V
            part = line.split()
            part2 = part[-1].split('(')

            func_name = part2[0]

            if func_name.startswith('access'):
                self.java_access = func_name

        elif line.startswith('end method', 1):
            self.access[self.java_access] = self.cur_access
            self.java_access = None

    def do_parent_command(self, line):
        if line.startswith('iget'):
            self.do_parent_put_get(line)
        elif line.startswith('sget'):
            self.do_parent_static_put_get(line)

    def do_parent_put_get(self, line):  # fix
        # iput-object v2, p0, Lcom/tutor/apkinstaller/ApkInstaller;->apkWeb:Landroid/webkit/WebView;
        line = line.replace(', ', ',')
        part = line.split()
        part2 = part[1].split(',')
        cls = self.make_class(part2[2])
        field = self.make_field(part2[2])
        self.cur_access = cls + '.' + 'this.' + field

    def do_parent_static_put_get(self, line):  # fix
        # sput-object v1, Lcom/moji/mjweather/activity/AddCityActivity;->mHotCitys:[Ljava/lang/String;
        line = line.replace(', ', ' ')
        part = line.split()
        cls = self.make_class(part[2])
        field = self.make_field(part[2])
        self.cur_access = cls + '.' + 'this.' + field


def list_file(dir_name):
    files = []
    try:
        ls = os.listdir(dir_name)
    except FileNotFoundError:
        print('dir access deny')
    else:
        for l in ls:
            filename = os.path.join(dir_name, l)
            if os.path.isdir(filename):
                file_names = list_file(filename)
                for filename in file_names:
                    files.append(filename)
            else:
                files.append(filename)

    return files


def to_java(file_smali, file_java):
    sm = SmaliFile(file_smali)
    sm.scan_file()
    sm.to_java(file_java)


def to_javas(dir_s, dir_j):
    lists = list_file(dir_s)

    for file_smali in lists:
        file_path = os.path.dirname(file_smali)
        file_name = os.path.basename(file_smali)
        [file_name, ext] = os.path.splitext(file_name)

        path_file_name = os.path.join(file_path, file_name)
        if ext == '.smali':
            print('FileName:' + file_smali)
            file_java = path_file_name.replace(dir_s, dir_j, 1) + '.java'
            path = os.path.dirname(file_java)
            if not os.path.isdir(path):
                os.makedirs(path)

            to_java(file_smali, file_java)


if __name__ == "__main__":
    if len(sys.argv) == 3:
        dir_smali = sys.argv[1]
        dir_java = sys.argv[2]
    elif len(sys.argv) == 2:
        dir_smali = sys.argv[1]
        dir_java = dir_smali
    else:
        dir_smali = 'smali'
        dir_java = 'smali'
        if not os.path.exists(dir_smali):
            print('smali2java [input dir] [output dir]')
            print('version: 2.00')
            exit()

    to_javas(dir_smali, dir_java)

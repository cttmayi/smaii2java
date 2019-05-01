import re


NUM = '(\d+)'
NUM_16 = '([\dx]+)'
ATTR = '((\w+ +)*)'
CLS = '(L[\w\d/\$]+;)'
VAR = '([\w\d\$]+)'
VT = '([\w/;\[]+)'
FUNC = '([\w\<\>]+)'
PARAMS = '([\[a-zA-Z\$/;]*)'
FT = '([\w/;]+)'
REG = '(\w\d)'
LBL = ':([\w\d]+)'

GS_DOT = [
    # .line 84
    ['.line', ['\.line +', NUM], ['NUM']],
    # .class public Landroidx/activity/ComponentActivity;
    ['.class', ['\.class +', ATTR, CLS], ['ATTR', None, 'CLS']],
    # .super Landroid/text/TextWatcher;
    ['.super', ['\.super +', CLS], ['CLS']],
    # .implements Landroid/text/TextWatcher;
    ['.implements', ['\.implements +', CLS], ['CLS']],
    # .field private static final COLUMN_INDEX_FIRST:I = 0x0
    ['.field', ['\.field +', ATTR, VAR, ':', VT, '( += +', NUM_16, ')*'], ['ATTR', None, 'VAR', 'VT', None, 'VAL']],
    # .end field
    ['.end field', None, None],
    # .method public static main([Ljava/lang/String;)V
    ['.method', ['\.method +', ATTR, FUNC, '\(', PARAMS, '\)', FT], ['ATTR', None, 'FUNC', 'PARAMS', 'FT']],
    # .end method
    ['.end method', None, None],
    # .parameter "x0"
    ['.parameter', ['\.parameter +"', VAR, '"'], ['VAR']],
    # .param p0, "feedbackType"    # I   @baksmali
    ['.param', ['\.param +', REG, '(, +"', VAR, '")*'], ['REG', None, 'VAR']],
    # .end param
    ['.end param', None, None],
    # .locals 3
    ['.locals', ['\.locals +' + NUM], ['NUM']],
    # .local v0, bundle:Landroid/os/Bundle;
    ['.local', ['.local +', REG, ' +', VAR + ':' + VT], ['REG', 'VAR', 'VT']],
    # .end local v0           #cityName:Ljava/lang/String;
    ['.end local', ['.end local +', REG,], ['REG']],

    ['.array-data', None, None],
    ['.end array-data', None, None],
    ['.annotation', None, None],
    ['.end annotation', None, None],
    ['.source', None, None],
    ['.registers', None, None],

    # .sparse-switch
    ['.sparse-switch', None, None],
    ['.end sparse-switch', None, None],
    # .packed-switch 0x1
    ['.packed-switch', ['\.packed-switch +', NUM_16], ['NUM']],
    ['.end packed-switch', None, None],
    # '.catchall {:try_start_0 .. :try_end_0} :catchall_0'
    ['.catchall', ['\.catchall +{', LBL, ' +\.\. +', LBL, '} +', LBL], ['LBL_TS', 'LBL_TE', 'LBL_C']],
    # .catch Ljava/lang/Exception; {:try_start_7 .. :try_end_7} :catch_7
    ['.catch', ['\.catch +', CLS, ' +{', LBL, ' +\.\. +', LBL, '} +', LBL], ['CLS', 'LBL_TS', 'LBL_TE', 'LBL_C']],
    # .enum Landroidx/annotation/RestrictTo$Scope;->LIBRARY:Landroidx/annotation/RestrictTo$Scope;
    ['.enum', None, None],
]


for gs in GS_DOT:
    if gs[1] is not None:
        gs[1] = ''.join(gs[1])


def get_attr(attr):
    ret = attr.split()
    return ret


ATTR_T = {
        'ATTR': get_attr,
    }


def dot_to(line):
    return to(line, GS_DOT)


def to(line, gs):
    ret = {}
    for g in gs:
        g_start = g[0]
        g_pattern = g[1]
        g_keys = g[2]
        if line.startswith(g_start):
            ret['CMD'] = g_start
            if g_pattern is not None:
                mat = re.match(g_pattern, line)
                if mat:
                    groups = mat.groups()
                    for i in range(len(g_keys)):
                        key = g_keys[i]
                        value = groups[i]
                        if value is not None and key is not None:
                            ret[key] = value.strip()
                            if key in ATTR_T:
                                ret[key] = ATTR_T[key](ret[key])
            return ret

    return None


if __name__ == "__main__":
    lines = [
        ['.line 84',
            {'NUM': '84'}],
        ['.class public Landroidx/activity/ComponentActivity;',
            {'CLS': 'Landroidx/activity/ComponentActivity;'}],
        ['.super Landroid/text/TextWatcher;',
            {'CLS': 'Landroid/text/TextWatcher;'}],
        ['.implements Landroid/text/TextWatcher;',
            {'CLS': 'Landroid/text/TextWatcher;'}],
        ['.field private static final COLUMN_INDEX_FIRST:I = 0x0',
            {'VAR': 'COLUMN_INDEX_FIRST', 'VAL': '0x0', 'ATTR': ['private', 'static', 'final']}],
        ['.field COLUMN_INDEX_FIRST:I',
            {'VAR': 'COLUMN_INDEX_FIRST', 'ATTR': []}],
        ['.field private static final COLUMN_INDEX_FIRST:I',
            {'VAR': 'COLUMN_INDEX_FIRST'}],
        ['.field private final mLifecycleRegistry:Landroidx/lifecycle/LifecycleRegistry;',
         {'VAR': 'mLifecycleRegistry', 'VT': 'Landroidx/lifecycle/LifecycleRegistry;'}],
        ['.end field',
            {'CMD': '.end field'}],
        ['.method public static main([Ljava/lang/String;)V',
            {'FUNC': 'main', 'PARAMS': '[Ljava/lang/String;', 'FT': 'V', 'ATTR': ['public', 'static']}],
        ['.param p0, "feedbackType"    # I   @baksmali',
            {'REG': 'p0', 'VAR': 'feedbackType'}],
        ['.param p1    # Landroid/os/Bundle;',
            {'REG': 'p1', 'VAR': None}],
        ['.end param',
            {'CMD': '.end param'}],

        ['.catch Landroid/os/RemoteException; {:try_start_0 .. :try_end_0} :catch_0', None],
        ['.catchall {:try_start_0 .. :try_end_0} :catchall_0', None],
        ['.catch Ljava/lang/NoSuchFieldException; {:try_start_0 .. :try_end_0} :catch_0',
            {'CLS': 'Ljava/lang/NoSuchFieldException;'}],
        ['.end packed-switch', None],
        ['.enum Landroidx/annotation/RestrictTo$Scope;->LIBRARY:Landroidx/annotation/RestrictTo$Scope;', None],

    ]

    total = 0
    pass_total = 0

    for one_line in lines:
        total = total + 1
        l_q = one_line[0]
        l_a = one_line[1]
        m = dot_to(l_q)
        is_correct = True
        if m is None:
            is_correct = False
        else:
            if l_a is not None:
                for a_key in l_a.keys():
                    ans = l_a[a_key]
                    if a_key in m.keys():
                        if l_a[a_key] != m[a_key]:
                            is_correct = False
                            break
                    else:
                        if ans is not None:
                            is_correct = False
                            break
        if not is_correct:
            print('[FAIL]', l_q)
            print('\tIt should be', l_a, 'but it\'s', m)
        else:
            pass_total = pass_total + 1
    print('PASS(%d/%d)' % (pass_total, total))

import re


NUM = '(\d+)'
NUM_16 = '(0x[\da-fA-F]+)'
ATTR = '((\w+ +)*)'
CLS = '(L[\w\d/\$]+;)'
VAR = '([\w\d\$]+)'
VT = '([\w/;\[]+)'
FUNC = '([\w\<\>]+)'
PARAMS = '([\[a-zA-Z\$/;]*)'
FT = '([\w/;]+)'
REG = '(\w\d+)'
LBL = ':([\w\d]+)'
REGS = '([\w\d ,]+)'
STRING = '(\".+\")'

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
    ['.end field'],
    # .method public static main([Ljava/lang/String;)V
    ['.method', ['\.method +', ATTR, FUNC, '\(', PARAMS, '\)', FT], ['ATTR', None, 'FUNC', 'PARAMS', 'FT']],
    # .end method
    ['.end method'],
    # .parameter "x0"
    ['.parameter', ['\.parameter +"', VAR, '"'], ['VAR']],
    # .param p0, "feedbackType"    # I   @baksmali
    ['.param', ['\.param +', REG, '(, +"', VAR, '")*'], ['REG', None, 'VAR']],
    # .end param
    ['.end param'],
    # .locals 3
    ['.locals', ['\.locals +' + NUM], ['NUM']],
    # .local v0, bundle:Landroid/os/Bundle;
    ['.local', ['.local +', REG, ' +', VAR + ':' + VT], ['REG', 'VAR', 'VT']],
    # .end local v0           #cityName:Ljava/lang/String;
    ['.end local', ['.end local +', REG,], ['REG']],

    ['.array-data'],
    ['.end array-data'],
    ['.annotation'],
    ['.end annotation'],
    ['.source'],
    ['.registers'],

    # .sparse-switch
    ['.sparse-switch'],
    ['.end sparse-switch'],
    # .packed-switch 0x1
    ['.packed-switch', ['\.packed-switch +', NUM_16], ['NUM']],
    ['.end packed-switch'],
    # '.catchall {:try_start_0 .. :try_end_0} :catchall_0'
    ['.catchall', ['\.catchall +{', LBL, ' +\.\. +', LBL, '} +', LBL], ['LBL_TS', 'LBL_TE', 'LBL_C']],
    # .catch Ljava/lang/Exception; {:try_start_7 .. :try_end_7} :catch_7
    ['.catch', ['\.catch +', CLS, ' +{', LBL, ' +\.\. +', LBL, '} +', LBL], ['CLS', 'LBL_TS', 'LBL_TE', 'LBL_C']],
    # .enum Landroidx/annotation/RestrictTo$Scope;->LIBRARY:Landroidx/annotation/RestrictTo$Scope;
    ['.enum'],
]

GS_CMD = [
    # 'invoke-super {p0, p1}, Landroid/app/Activity;->onCreate(Landroid/os/Bundle;)V'
    # invoke-direct {v0}, Ljava/lang/RuntimeException;-><init>()V
    # invoke-static {p1}, Landroid/text/TextUtils;->isEmpty(Ljava/lang/CharSequence;)Z
    # invoke-virtual {v2, v0}, Landroid/webkit/WebView;->loadUrl(Ljava/lang/String;)V
    ['invoke', ['invoke\-', '(\w+)', ' +\{', REGS, '\}, +', CLS, '\-\>', FUNC], ['TP', 'REGS', 'CLS', 'FUNC']],
    # const/high16 v2, 0x7f03
    # const/high16 p0, 0x3f800000    # 1.0f
    ['const', ['const\/', '(high\d+) +', REG, ', +', NUM_16], ['TP', 'REG', 'NUM']],
    # const-string v2, ", "
    ['const', ['const\-string +', REG, ', +', STRING], ['REG', 'STR']],

    # iget/iput
    # iput-object v2, p0, Lcom/tutor/apkinstaller/ApkInstaller;->apkWeb:Landroid/webkit/WebView;
    ['i', ['i(\w+)\-object +', REG, ', +', REG, ', +', CLS, '\-\>', VAR, ':', CLS],
        ['TP', 'REG_V', 'REG_O', 'CLS', 'VAR', 'VAR_C']],

    # sget/sput
    # sput-object v1, Lcom/moji/mjweather/activity/AddCityActivity;->mHotCitys:[Ljava/lang/String;
    ['s', ['s(\w+)\-object +', REG, ', +', CLS, '\-\>', VAR, ':', VT],
     ['TP', 'REG', 'CLS', 'VAR', 'VT']],

    # aget/aput
    # aget-object v3, v3, v0
    ['a', ['a(\w+)\-object +', REG, ', +', REG, ', +', REG], ['REG', 'REG_AR', 'REG_ID']],

    # move-result-object v2
    # move-exception v0
    ['move', ['move\-([\w\-]+) +', REG], ['TP', 'REG']],
    # move-object/from16 v0, p0
    ['move-object', ['move\-object\/(from\d+) +', REG, ', +', REG], ['TP', 'REG']],

    # return-void
    ['return-void'],
    # return-object v0
    ['return-object', ['return\-object +', REG], ['REG']],

    # goto :goto_0
    ['goto', ['goto +', LBL], ['LBL']],

    # new-instance v1, Lcom/moji/mjweather/activity/AddCityActivity$1;
    ['new-instance', ['new\-instance +', REG, ', +', CLS], ['REG', 'CLS']],
    # new-array v1, v1, [Ljava/lang/String;
    ['new-array', ['new\-array +', REG, ', +', REG, ', +', VT], ['REG_O', 'REG_L', 'VT']],

    # fill-array-data v0, :array_0
    ['fill-array-data', ['fill\-array\-data +', REG, ', +', LBL], ['REG', 'LBL']],

    # if-nez v1, :cond_0
    # if-ge v0, v1, :cond_1
    ['if', ['if\-(\w+) +', REGS, ', +', LBL], ['TP', 'REGS', 'LBL']],

    # check-cast v1, Landroid/widget/ImageButton;
    ['check-cast', ['check\-cast +', REG, ', +', CLS], ['REG', 'CLS']],

    # add/mul/sub/div/rem/add/or/xor/shl/shr/ushr
    # mul-double/2addr v3, v5


    # add-int/lit8 v9, v8, 0x1

    # not/neg
    # not-int vx, vy

    # cmpl-float v13, v11, v7
    ['cmpl', ['cmpl\-(\w+) +', REG, ', +', REG, ', +', REG], ['TP', 'REG_1', 'REG_2', 'REG_3']],

    # sparse-switch v1, :sswitch_data_0
    # packed-switch p0, :pswitch_data_0
    ['sparse-switch', ['sparse\-switch +', REG, ', +', LBL], ['REG', 'LBL']],
    ['packed-switch', ['packed\-switch +', REG, ', +', LBL], ['REG', 'LBL']],

    # array-length v1, v1
    ['array-length', ['array\-length +', REG, ', +', REG], ['REG_1', 'REG_2']],

    # throw v0
    ['throw', ['throw +', REG], ['REG']],

    # instance-of v8, v7, Landroid/widget/TextView;
    ['instance-of', ['instance\-of +', REG, ', +', REG, ', +', CLS], ['REG', 'CLS']],

    # monitor-enter p0
    ['monitor-enter', ['monitor\-enter +', REG], ['REG']],

    # int-to-double v3, v3
    ['', ['(\w+)\-(to)\-(\w+) +', REG, ', +', REG], ['TP_1', 'CMD', 'TP_2', 'REG_1', 'REG_2']],


]


for gs in GS_DOT:
    if len(gs) >= 2:
        gs[1] = ''.join(gs[1])
    else:
        gs.append(None)
        gs.append(None)

for gs in GS_CMD:
    if len(gs) >= 2:
        gs[1] = ''.join(gs[1])
    else:
        gs.append(None)
        gs.append(None)


def __get_attr(attr):
    ret = attr.split()
    return ret


ATTR_T = {
        'ATTR': __get_attr,
    }


def to_op(line):
    if line.startswith('.'):
        ret = to(line, GS_DOT)
    else:
        ret = to(line, GS_CMD)
    return ret


def to(line, gs):
    ret = {}
    for g in gs:
        g_start = g[0]
        if line.startswith(g_start):
            g_pattern = g[1]
            if g_pattern is not None:
                mat = re.match(g_pattern, line)
                if mat:
                    ret['CMD'] = g_start
                    g_keys = g[2]
                    groups = mat.groups()
                    for i in range(len(g_keys)):
                        key = g_keys[i]
                        value = groups[i]
                        if value is not None and key is not None:
                            ret[key] = value.strip()
                            if key in ATTR_T:
                                ret[key] = ATTR_T[key](ret[key])
                else:
                    continue
            else:
                ret['CMD'] = g_start
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

        ['invoke-super {p0, p1}, Landroid/app/Activity;->onCreate(Landroid/os/Bundle;)V', None],
        ['invoke-direct {v0}, Ljava/lang/RuntimeException;-><init>()V', None],
        ['invoke-static {p1}, Landroid/text/TextUtils;->isEmpty(Ljava/lang/CharSequence;)Z', None],
        ['invoke-virtual {v2, v0}, Landroid/webkit/WebView;->loadUrl(Ljava/lang/String;)V',
            {'TP': 'virtual', 'CLS': 'Landroid/webkit/WebView;'}],

        ['const/high16 v2, 0x7f03', None],
        ['const/high16 p0, 0x3f800000    # 1.0f',
            {'TP': 'high16', 'NUM': '0x3f800000'}],
        ['const-string v2, ", "', None],

        ['iput-object v2, p0, Lcom/tutor/apkinstaller/ApkInstaller;->apkWeb:Landroid/webkit/WebView;', None],
        ['sput-object v1, Lcom/moji/mjweather/activity/AddCityActivity;->mHotCitys:[Ljava/lang/String;', None],
        ['aget-object v3, v3, v0', None],

        ['move-result-object v2', None],
        ['move-exception v0', None],
        ['move-object/from16 v0, p0', None],

        ['return-void', None],
        ['return-object v0', None],

        ['goto :goto_0', None],

        ['new-instance v1, Lcom/moji/mjweather/activity/AddCityActivity$1;', None],
        ['new-array v1, v1, [Ljava/lang/String;', None],

        ['fill-array-data v0, :array_0', None],

        ['if-nez v1, :cond_0', None],
        ['if-ge v0, v1, :cond_1', None],

        ['check-cast v1, Landroid/widget/ImageButton;', None],

        ['mul-double/2addr v3, v5', None],
        ['add-int/lit8 v9, v8, 0x1', None],

        ['not-int vx, vy', None],

        ['cmpl-float v13, v11, v7', None],

        ['sparse-switch v1, :sswitch_data_0', None],
        ['packed-switch p0, :pswitch_data_0', None],

        ['array-length v1, v1', None],

        ['int-to-double v3, v3', None],

        ['throw v0', None],

        ['instance-of v8, v7, Landroid/widget/TextView;', None],

        ['monitor-enter p0', {'REG': 'p0'}],

    ]

    total = 0
    pass_total = 0

    for one_line in lines:
        total = total + 1
        l_q = one_line[0]
        l_a = one_line[1]
        m = to_op(l_q)
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
            if m is None:
                print('\tIt\'s', m)
            else:
                print('\tIt should be', l_a, 'but it\'s', m)
        else:
            pass_total = pass_total + 1
    print('PASS(%d/%d)' % (pass_total, total))

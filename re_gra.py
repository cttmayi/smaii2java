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
    [['.line'], [' +', NUM], ['NUM']],
    # .class public Landroidx/activity/ComponentActivity;
    [['.class'], [' +', ATTR, CLS], ['ATTR', None, 'CLS']],
    # .super Landroid/text/TextWatcher;
    [['.super'], [' +', CLS], ['CLS']],
    # .implements Landroid/text/TextWatcher;
    [['.implements'], [' +', CLS], ['CLS']],
    # .field private static final COLUMN_INDEX_FIRST:I = 0x0
    [['.field'], [' +', ATTR, VAR, ':', VT, '( += +', NUM_16, ')*'], ['ATTR', None, 'VAR', 'VT', None, 'VAL']],
    [['.end field']],
    # .method public static main([Ljava/lang/String;)V
    [['.method'], [' +', ATTR, FUNC, '\(', PARAMS, '\)', FT], ['ATTR', None, 'FUNC', 'PARAMS', 'FT']],
    [['.end method']],
    # .parameter "x0"
    [['.parameter'], [' +"', VAR, '"'], ['VAR']],
    # .param p0, "feedbackType"    # I   @baksmali
    [['.param'], [' +', REG, '(, +"', VAR, '")*'], ['REG', None, 'VAR']],
    [['.end param']],
    # .locals 3
    [['.locals'], [' +' + NUM], ['NUM']],
    # .local v0, bundle:Landroid/os/Bundle;
    [['.local'], [' +', REG, ' +', VAR + ':' + VT], ['REG', 'VAR', 'VT']],
    # .end local v0           #cityName:Ljava/lang/String;
    [['.end local'], [' +', REG,], ['REG']],

    [['.array-data']],
    [['.end array-data']],
    [['.annotation']],
    [['.end annotation']],
    [['.source']],
    [['.registers']],

    # .sparse-switch
    [['.sparse-switch']],
    [['.end sparse-switch']],
    # .packed-switch 0x1
    [['.packed-switch'], [' +', NUM_16], ['NUM']],
    [['.end packed-switch']],
    # '.catchall {:try_start_0 .. :try_end_0} :catchall_0'
    [['.catchall'], [' +{', LBL, ' +\.\. +', LBL, '} +', LBL], ['LBL_TS', 'LBL_TE', 'LBL_C']],
    # .catch Ljava/lang/Exception; {:try_start_7 .. :try_end_7} :catch_7
    [['.catch'], [' +', CLS, ' +{', LBL, ' +\.\. +', LBL, '} +', LBL], ['CLS', 'LBL_TS', 'LBL_TE', 'LBL_C']],
    # .enum Landroidx/annotation/RestrictTo$Scope;->LIBRARY:Landroidx/annotation/RestrictTo$Scope;
    [['.enum']],
]

GS_CMD = [
    # 'invoke-super {p0, p1}, Landroid/app/Activity;->onCreate(Landroid/os/Bundle;)V'
    # invoke-direct {v0}, Ljava/lang/RuntimeException;-><init>()V
    # invoke-static {p1}, Landroid/text/TextUtils;->isEmpty(Ljava/lang/CharSequence;)Z
    # invoke-virtual {v2, v0}, Landroid/webkit/WebView;->loadUrl(Ljava/lang/String;)V
    [['invoke'], ['\-', '(\w+)', ' +\{', REGS, '\}, +', CLS, '\-\>', FUNC], ['TP', 'REGS', 'CLS', 'FUNC']],
    # const/high16 v2, 0x7f03
    # const/high16 p0, 0x3f800000    # 1.0f
    [['const'], ['\/', '(high\d+) +', REG, ', +', NUM_16], ['TP', 'REG', 'NUM']],
    # const-string v2, ", "
    [['const-string'], [' +', REG, ', +', STRING], ['REG', 'STR']],

    # iput-object v2, p0, Lcom/tutor/apkinstaller/ApkInstaller;->apkWeb:Landroid/webkit/WebView;
    [['iget', 'iput'], ['\-object +', REG, ', +', REG, ', +', CLS, '\-\>', VAR, ':', CLS],
        ['REG_V', 'REG_O', 'CLS', 'VAR', 'VAR_C']],

    # sput-object v1, Lcom/moji/mjweather/activity/AddCityActivity;->mHotCitys:[Ljava/lang/String;
    [['sget', 'sput'], ['\-object +', REG, ', +', CLS, '\-\>', VAR, ':', VT],
        ['REG', 'CLS', 'VAR', 'VT']],

    # aget-object v3, v3, v0
    [['aget', 'aput'], ['\-object +', REG, ', +', REG, ', +', REG], ['REG', 'REG_AR', 'REG_ID']],

    # move-result-object v2
    # move-exception v0
    [['move'], ['\-([\w\-]+) +', REG], ['TP', 'REG']],
    # move-object/from16 v0, p0
    [['move-object'], ['\/(from\d+) +', REG, ', +', REG], ['TP', 'REG']],

    # return-void
    [['return-void']],
    # return-object v0
    [['return-object'], [' +', REG], ['REG']],

    # goto :goto_0
    [['goto'], [' +', LBL], ['LBL']],

    # new-instance v1, Lcom/moji/mjweather/activity/AddCityActivity$1;
    [['new-instance'], [' +', REG, ', +', CLS], ['REG', 'CLS']],
    # new-array v1, v1, [Ljava/lang/String;
    [['new-array'], [' +', REG, ', +', REG, ', +', VT], ['REG_O', 'REG_L', 'VT']],

    # fill-array-data v0, :array_0
    [['fill-array-data'], [' +', REG, ', +', LBL], ['REG', 'LBL']],

    # if-nez v1, :cond_0
    # if-ge v0, v1, :cond_1
    [['if'], ['\-(\w+) +', REGS, ', +', LBL], ['TP', 'REGS', 'LBL']],

    # check-cast v1, Landroid/widget/ImageButton;
    [['check-cast'], [' +', REG, ', +', CLS], ['REG', 'CLS']],



    # cmpl-float v13, v11, v7
    [['cmpl-'], ['(\w+) +', REG, ', +', REG, ', +', REG], ['TP', 'REG_1', 'REG_2', 'REG_3']],

    # sparse-switch v1, :sswitch_data_0
    # packed-switch p0, :pswitch_data_0
    [['sparse-switch', 'packed-switch'], [' +', REG, ', +', LBL], ['REG', 'LBL']],

    # array-length v1, v1
    [['array-length'], [' +', REG, ', +', REG], ['REG_1', 'REG_2']],

    # throw v0
    [['throw'], [' +', REG], ['REG']],

    # instance-of v8, v7, Landroid/widget/TextView;
    [['instance-of'], [' +', REG, ', +', REG, ', +', CLS], ['REG', 'CLS']],

    # monitor-enter p0
    [['monitor-enter'], [' +', REG], ['REG']],

    # int-to-double v3, v3
    [['int'], ['-to\-(\w+) +', REG, ', +', REG], ['TP', 'REG_1', 'REG_2']],

    # add/mul/sub/div/rem/add/or/xor/shl/shr/ushr
    # mul-double/2addr v3, v5
    # mul-double v0, v0, v2
    # add-int/lit8 v9, v8, 0x1
    [['add', 'mul', 'sub', 'div', 'rem', 'add', 'or', 'xor', 'shl', 'shr', 'ushr'],
        ['\-(\w+)(/([\w\d]+))* +', REG, ', +', REG, '(, +', NUM_16, ')*'],
        ['RV', None, 'RN', 'REG_1', 'REG_2', None, 'NUM']],

    # not/neg

]


def make_gra(gfs):
    gra_s = []
    for fmt in gfs:
        for st in fmt[0]:
            gra = [st]
            if len(fmt) >= 2:
                gra.append(st.replace('.', '\\.') + ''.join(fmt[1]))
            else:
                gra.append(None)
            if len(fmt) >= 3:
                gra.append(fmt[2])
            else:
                gra.append(None)
            gra_s.append(gra)
    return gra_s


GS_DOT = make_gra(GS_DOT)
GS_CMD = make_gra(GS_CMD)


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
    ret = None
    for g in gs:
        g_start = g[0]
        if line.startswith(g_start):
            g_pattern = g[1]
            if g_pattern is not None:
                mat = re.match(g_pattern, line)
                if mat:
                    ret = {'CMD': g_start}
                    g_keys = g[2]
                    groups = mat.groups()
                    for i in range(len(g_keys)):
                        key = g_keys[i]
                        value = groups[i]
                        if value is not None and key is not None:
                            ret[key] = value.strip()
                            if key in ATTR_T:
                                ret[key] = ATTR_T[key](ret[key])
                    break
                else:
                    continue
            else:
                ret = {'CMD': g_start}
                break
    return ret


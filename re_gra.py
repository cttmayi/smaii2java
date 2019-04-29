import re


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
        {'VAR': 'COLUMN_INDEX_FIRST', 'VAL': '0x0'}],
    ['.field COLUMN_INDEX_FIRST:I',
        {'VAR': 'COLUMN_INDEX_FIRST'}],
    ['.field private static final COLUMN_INDEX_FIRST:I',
        {'VAR': 'COLUMN_INDEX_FIRST'}],
    ['.field private final mLifecycleRegistry:Landroidx/lifecycle/LifecycleRegistry;',
     {'VAR': 'mLifecycleRegistry', 'VT': 'Landroidx/lifecycle/LifecycleRegistry;'}],
    ['.end field',
        {'CMD': '.end field'}],
    ['.method public static main([Ljava/lang/String;)V',
        {'FUN': 'main', 'PARAMS': '[Ljava/lang/String;', 'FT': 'V'}],
    ['.param p0, "feedbackType"    # I   @baksmali',
        {'REG': 'p0', 'VAR': 'feedbackType'}],
    ['.param p1    # Landroid/os/Bundle;',
        {'REG': 'p1', 'VAR': None}],
]


class ReGra:
    NUM = '(\d+)'
    NUM_16 = '([\dx]+)'
    ATTS = '((\w+ +)*) *'
    CLS = '(L[a-zA-Z/]+;)'
    VAR = '(\w+)'
    VT = '([\w/;]+)'
    FUN = '(\w+)'
    PARAMS = '([\[a-zA-Z/;]*)'
    FT = '([\w/;]+)'
    REG = '(\w\d)'

    GS = [
        # .line 84
        ['.line', ['\.line +', NUM], ['NUM']],
        # .class public Landroidx/activity/ComponentActivity;
        ['.class', ['\.class +', ATTS, CLS], ['ATTS', None, 'CLS']],
        # .super Landroid/text/TextWatcher;
        ['.super', ['\.super +', CLS], ['CLS']],
        # .implements Landroid/text/TextWatcher;
        ['.implements', ['\.implements +', CLS], ['CLS']],
        # .field private static final COLUMN_INDEX_FIRST:I = 0x0
        ['.field', ['\.field +', ATTS, VAR, ':', VT, '( += +', NUM_16, ')*'], ['ATTS', None, 'VAR', 'VT', None, 'VAL']],
        # .end field
        ['.end field', None, None],
        # .method public static main([Ljava/lang/String;)V
        ['.method', ['\.method +', ATTS, FUN, '\(', PARAMS, '\)', FT], ['ATTS', None, 'FUN', 'PARAMS', 'FT']],
        # .end method
        ['.end method', None, None],
        # .param p0, "feedbackType"    # I   @baksmali
        ['.param', ['\.param +', REG, '(, +"', VAR, '")*'], ['REG', None, 'VAR']],
        # .end param
        ['.end param', None, None],

    ]

    def __init__(self):
        for gs in self.GS:
            if gs[1] is not None:
                gs[1] = ''.join(gs[1])
        pass

    @staticmethod
    def to(line):
        ret = {}
        for g in ReGra.GS:
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
                return ret

        return None


def main():
    total = 0
    pass_total = 0
    re_gra = ReGra()
    for one_line in lines:
        total = total + 1
        l_q = one_line[0]
        l_a = one_line[1]
        m = re_gra.to(l_q)
        is_correct = True
        if m is None:
            is_correct = False
        else:

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
            print('\t', m, l_a)
        else:
            pass_total = pass_total + 1
    print('PASS(%d/%d)' % (pass_total, total))

main()
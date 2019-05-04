# coding = utf-8
import unittest
import re_gra


class ReGraTest(unittest.TestCase):
    @staticmethod
    def setUPClass(cls):
        pass

    def setUp(self):
        pass

    @staticmethod
    def tearDownClass(cls):
        pass

    def tearDown(self):
        pass

    def test_to_dot(self):
        lines = [
            ['.line 84', {'NUM': '84'}],
            ['.class public Landroidx/activity/ComponentActivity;', {'CLS': 'Landroidx/activity/ComponentActivity;'}],
            ['.super Landroid/text/TextWatcher;', {'CLS': 'Landroid/text/TextWatcher;'}],
            ['.implements Landroid/text/TextWatcher;', {'CLS': 'Landroid/text/TextWatcher;'}],
            ['.field private static final COLUMN_INDEX_FIRST:I = 0x0',
             {'VAR': 'COLUMN_INDEX_FIRST', 'VAL': '0x0', 'ATTR': ['private', 'static', 'final']}],
            ['.field COLUMN_INDEX_FIRST:I', {'VAR': 'COLUMN_INDEX_FIRST', 'ATTR': []}],
            ['.field private static final COLUMN_INDEX_FIRST:I', {'VAR': 'COLUMN_INDEX_FIRST'}],
            ['.field private final mLifecycleRegistry:Landroidx/lifecycle/LifecycleRegistry;',
             {'VAR': 'mLifecycleRegistry', 'VT': 'Landroidx/lifecycle/LifecycleRegistry;'}],
            ['.end field', {'CMD': '.end field'}],
            ['.method public static main([Ljava/lang/String;)V',
             {'FUNC': 'main', 'PARAMS': '[Ljava/lang/String;', 'FT': 'V', 'ATTR': ['public', 'static']}],
            ['.param p0, "feedbackType"    # I   @baksmali', {'REG': 'p0', 'VAR': 'feedbackType'}],
            ['.param p1    # Landroid/os/Bundle;', {'REG': 'p1', 'VAR': None}], ['.end param', {'CMD': '.end param'}],

            ['.catch Landroid/os/RemoteException; {:try_start_0 .. :try_end_0} :catch_0', None],
            ['.catchall {:try_start_0 .. :try_end_0} :catchall_0', None],
            ['.catch Ljava/lang/NoSuchFieldException; {:try_start_0 .. :try_end_0} :catch_0',
             {'CLS': 'Ljava/lang/NoSuchFieldException;'}], ['.end packed-switch', None],
            ['.enum Landroidx/annotation/RestrictTo$Scope;->LIBRARY:Landroidx/annotation/RestrictTo$Scope;', None],

            ['invoke-super {p0, p1}, Landroid/app/Activity;->onCreate(Landroid/os/Bundle;)V', None],
            ['invoke-direct {v0}, Ljava/lang/RuntimeException;-><init>()V', None],
            ['invoke-static {p1}, Landroid/text/TextUtils;->isEmpty(Ljava/lang/CharSequence;)Z', None],
            ['invoke-virtual {v2, v0}, Landroid/webkit/WebView;->loadUrl(Ljava/lang/String;)V',
             {'TP': 'virtual', 'CLS': 'Landroid/webkit/WebView;'}],

            ['const/high16 v2, 0x7f03', None],
            ['const/high16 p0, 0x3f800000    # 1.0f', {'TP': 'high16', 'NUM': '0x3f800000'}],
            ['const-string v2, ", "', None],

            ['iput-object v2, p0, Lcom/tutor/apkinstaller/ApkInstaller;->apkWeb:Landroid/webkit/WebView;', None],
            ['sput-object v1, Lcom/moji/mjweather/activity/AddCityActivity;->mHotCitys:[Ljava/lang/String;', None],
            ['aget-object v3, v3, v0', None],

            ['move-result-object v2', None], ['move-exception v0', None], ['move-object/from16 v0, p0', None],

            ['return-void', None], ['return-object v0', None],
            ['goto :goto_0', None],

            ['new-instance v1, Lcom/moji/mjweather/activity/AddCityActivity$1;', None],
            ['new-array v1, v1, [Ljava/lang/String;', None],

            ['fill-array-data v0, :array_0', None],
            ['if-nez v1, :cond_0', None], ['if-ge v0, v1, :cond_1', None],
            ['check-cast v1, Landroid/widget/ImageButton;', {'CLS': 'Landroid/widget/ImageButton;'}],

            ['mul-double/2addr v3, v5', None], ['add-int/lit8 v9, v8, 0x1', {'NUM': '0x1'}],
            ['mul-double v0, v0, v2', None],

            ['cmpl-float v13, v11, v7', {'REG_1': 'v13'}],
            ['sparse-switch v1, :sswitch_data_0', None], ['packed-switch p0, :pswitch_data_0', None],
            ['array-length v1, v1', None],
            ['int-to-double v3, v3', None],
            ['throw v0', None],
            ['instance-of v8, v7, Landroid/widget/TextView;', None],
            ['monitor-enter p0', {'REG': 'p0'}],

        ]

        for one_line in lines:
            line_smali = one_line[0]
            expected = one_line[1]
            result = re_gra.to_op(line_smali)

            self.assertIsNotNone(result, line_smali + '(Not Match)')
            if expected is not None:
                result2 = {}
                for a_key in expected.keys():
                    if a_key in result.keys():
                        result2[a_key] = result[a_key]
                    else:
                        result2[a_key] = None
                self.assertEqual(expected, result2, line_smali + '(Error)')


if __name__ == '__main__':
    unittest.main()

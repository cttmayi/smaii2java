# smali2java

------------





Android SMALI 文件翻译为Java代码

## 使用方法

利用apktool先把APK转换为SMALI代码, 然后执行如下命令(注: 使用Python 3)

`python smali2java.py [SMALI目录] [Java目录]`

## 使用效果

```
# virtual methods
.method public addOnBackPressedCallback(Landroidx/activity/OnBackPressedCallback;)V
    .locals 2
    .param p1    # Landroidx/activity/OnBackPressedCallback;
        .annotation build Landroidx/annotation/NonNull;
        .end annotation
    .end param
    .annotation runtime Ljava/lang/Deprecated;
    .end annotation

    .line 325
    iget-object v0, p0, Landroidx/activity/ComponentActivity;->mOnBackPressedCallbackCancellables:Ljava/util/WeakHashMap;

    .line 326
    invoke-virtual {p0}, Landroidx/activity/ComponentActivity;->getOnBackPressedDispatcher()Landroidx/activity/OnBackPressedDispatcher;

    move-result-object v1

    .line 327
    invoke-virtual {v1, p0, p1}, Landroidx/activity/OnBackPressedDispatcher;->addCallback(Landroidx/lifecycle/LifecycleOwner;Landroidx/activity/OnBackPressedCallback;)Landroidx/arch/core/util/Cancellable;

    move-result-object v1

    .line 325
    invoke-virtual {v0, p1, v1}, Ljava/util/WeakHashMap;->put(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;

    return-void
.end method
```

转换后的结果如下

```P
	void addOnBackPressedCallback(OnBackPressedCallback ){
//line 325
		v0 = this.mOnBackPressedCallbackCancellables;
//line 326
		v1 = this.getOnBackPressedDispatcher();;
//line 327
		v1 = v1.addCallback(this, );;
//line 325
		v0.put(, v1);
		return;
	}
```






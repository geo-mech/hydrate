### 说明

在这个文件夹中，存放一些最接近用户应用层的功能和配置。

### seepage 模块

基于Seepage类建模的配置（新版本）。在Seepage中动态地注册键来定义属性。

这个模块是进行热/流/化耦合计算的核心。

### capillary 模块

毛管力模块。两个不同的流体或者组分，在浓度差的驱动下扩散的过程。

此模块会在seepage模块中被调用。

### attr_keys 模块

用以辅助定义和管理动态的属性ID.

### TherFlowConfig 模块

旧版本地配置，与seepage模块不同，旧版本的TherFlowConfig使用静态的属性ID.

注意：此模块不再更新. 后续尽可能基于 seepage模块来建模. 

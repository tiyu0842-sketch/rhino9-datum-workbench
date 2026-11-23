# Rhino 9 全量命令索引

> **数据源**：运行中 Rhino 9.1.26314.9001，经 `Rhino.Commands.Command.GetCommandNames(True, False)` 导出，**不是网页抄录**。
> `loaded=True` 得 1052 条；`loaded=False` 得 **1256 条**（含未加载插件的注册命令）。
> 官网无全量索引页：`index.htm` 是跳转页，`commands/` 目录 403；`Untrim` 等是 `trim.htm` 的锚点而非独立页。
> 刷新方法：在 Rhino Python 里 exec `scripts/Export_Rhino_Commands.py`（路径可移植），再重跑分类生成。
> 官方用法入口：`https://docs.mcneel.com/rhino/9/help/en-us/commands/<小写命令名>.htm`；
> 中文版把 `en-us` 换成 `zh-cn` 或 `zh-tw`；主题分类页在 `.../seealso/sak_*.htm`。带浏览器 UA 才返回 200。

**注意**：命令名表是会话缓存，`FW2Panel` 等历史命令仍在表内 —— **命令名存在 ≠ 插件已加载 / 面板已注册**（见 E-016、E-018）。

## 1. 按功能域速查（可重叠，一条命令可出现在多个域）

| 功能域 | 条数 | 代表命令 |
|---|---:|---|
| 取消修剪 / 曲面修复 / 重缝 | 40 | `Cap`, `CreateSolid`, `DeleteFaces`, `DupFaceBorder`, `Explode`, `ExplodeBlock` |
| 布尔 / 倒角 / 孔 / 实体编辑 | 76 | `AddMissingBlockAttributeKeys`, `ArrayHole`, `ArrayHolePolar`, `Bend`, `Boolean2Objects`, `BooleanDifference` |
| 曲面 / 曲线生成 | 124 | `ApplyCrv`, `Arc`, `ArcBlend`, `ArrayCrv`, `ArrayCrvOld`, `ArrayCrvOnSrf` |
| 网格 Mesh | 97 | `AddNgonsToMesh`, `ApplyMesh`, `ApplyMeshUVN`, `ClearAllMeshes`, `ClearAnalysisMeshes`, `CollapseMeshEdge` |
| SubD | 31 | `CreaseSubDEdge`, `ExpandSubDEdges`, `ExtrudeSubD`, `LoftSubD`, `MatchSubD`, `OffsetSubD` |
| 选择 / 框选 / 子对象 | 141 | `ClearUndoSelection`, `DatumPlanePick`, `FWSelect`, `IntersectSelf`, `MeshSelfIntersect`, `MeshSelfSplit` |
| 显示 / 渲染 / 视图 | 142 | `3View`, `4View`, `AliasStyleLight`, `BackgroundBitmap`, `BatchRenderNamedViews`, `BringViewportToTop` |
| 工作平面 / 坐标 / 捕捉 | 54 | `ApplyPlanarMapping`, `AutoAlignCPlane`, `CPlane`, `CopyCPlaneSettingsToAll`, `CopyCPlaneToAll`, `DisableOsnap` |
| 图层 / 属性 / 对象管理 | 156 | `AddMissingBlockAttributeKeys`, `AddObjectsToBlock`, `AddToGroup`, `BatchRenderNamedViews`, `Block`, `BlockContent` |
| 标注 / 文字 / 出图 | 107 | `AlignClippingDrawings`, `AssignBlankTexture`, `BooleanIntersection`, `ClearClippingSections`, `ClippingDrawings`, `ClippingPlane` |
| 文件 / 导入导出 / 模板 | 92 | `AlignProfiles`, `AttachGHSData`, `Audit`, `Audit3dmFile`, `Autosave`, `CheckNewObjects` |
| 分析 / 检测 / 测量 | 57 | `Angle`, `ApplySurfaceMapping`, `Area`, `AreaCentroid`, `AreaMoments`, `BakeMapping` |
| 变换 / 阵列 / 定位 | 98 | `Align`, `AlignClippingDrawings`, `AlignProfiles`, `AlignVertices`, `Array`, `ArrayCrv` |
| 历史 / 撤销 / 命令层 | 40 | `AliasStyle`, `AliasStyleDark`, `AliasStyleLight`, `AliasStyleRestore`, `Cancel`, `ClearUndo` |
| 面板 / 工具栏 / 选项 / UI | 26 | `CommandPrompt`, `DisplayCommandPrompt`, `DocumentProperties`, `DocumentPropertiesPage`, `ExportRuiFile`, `FW2Panel` |
| Grasshopper / 脚本 / 开发 | 56 | `AliasStyleLight`, `AttachGHSData`, `ChangeLightType`, `CurveThroughPolyline`, `CurveThroughPt`, `CurveThroughSrfControlPt` |
| 我们的插件 FW* | 21 | `FW`, `FW2`, `FW2Panel`, `FW2Recognize`, `FW2Restore`, `FWCancel` |
| 未归入任何域 | 296 | `3DFace`, `AI`, `About`, `AboutRhino`, `AcadSchemes`, `AddGuide` |

### 取消修剪 / 曲面修复 / 重缝（40）

`Cap` `CreateSolid` `DeleteFaces` `DupFaceBorder` `Explode` `ExplodeBlock`
`ExplodeText` `ExtractOriginalCaptives` `ExtractSrf` `Join` `JoinCopy` `JoinEdge`
`JoinText` `MergeCoplanarFace` `MergeFaces` `MergeSrf` `MeshTrim` `MoveUntrimmedEdge`
`MoveUntrimmedFace` `RebuildEdges` `RefitTrim` `ReplaceEdge` `ScreenCaptureToClipboard` `ScreenCaptureToFile`
`SelCaptives` `SelTrimmedSrf` `SelUntrimmedSrf` `ShrinkTrimmedSrf` `ShrinkTrimmedSrfToEdge` `SplitDisjointMesh`
`SplitFace` `Trim` `UnjoinEdge` `Untrim` `UntrimAll` `UntrimBorder`
`UntrimHoles` `ViewCaptureToClipboard` `ViewCaptureToFile` `WireCut`

### 布尔 / 倒角 / 孔 / 实体编辑（76）

`AddMissingBlockAttributeKeys` `ArrayHole` `ArrayHolePolar` `Bend` `Boolean2Objects` `BooleanDifference`
`BooleanIntersection` `BooleanSplit` `BooleanUnion` `Chamfer` `ChamferEdge` `ChamferSrf`
`ConvertTextToBlockAttribute` `CopyHole` `Crease` `CreaseSplitting` `CreaseSubDEdge` `CreateSolid`
`CurveBoolean` `DimCreaseAngle` `Distribute` `DivideAlongCreases` `DraftAngleAnalysis` `DraftAngleAnalysisOff`
`DraftAnglePoint` `DupMeshHoleBoundary` `ExportBlockAttributes` `ExtractMeshFacesByDraftAngle` `ExtrudeCrvTapered` `ExtrudeSrfTapered`
`FillMeshHole` `FillMeshHoles` `Fillet` `FilletCorners` `FilletEdge` `FilletSrf`
`FilletSrfCrv` `FilletSrfToRail` `Flow` `FlowAlongSrf` `MakeHole` `MeshBooleanDifference`
`MeshBooleanIntersection` `MeshBooleanSplit` `MeshBooleanUnion` `MeshEllipsoid` `MicroScribeCalibrateTip` `MicroScribeDeviceInfo`
`MicroScribeSelectTip` `MirrorHole` `MoveHole` `Offset` `OffsetCrvOnSrf` `OffsetMesh`
`OffsetMultiple` `OffsetNormal` `OffsetSrf` `OffsetSubD` `PlaceHole` `PushPull`
`RemoveCrease` `RevolvedHole` `Rib` `Ribbon` `RibbonOffset` `RotateHole`
`RoundHole` `SelMeshFacesByDraftAngle` `Shell` `SolidPtOn` `Taper` `Twist`
`UntrimHoles` `VariableChamferSrf` `VariableFilletSrf` `VariableOffsetSrf`

### 曲面 / 曲线生成（124）

`ApplyCrv` `Arc` `ArcBlend` `ArrayCrv` `ArrayCrvOld` `ArrayCrvOnSrf`
`ArrayLinear` `BlendCrv` `BlendEdge` `BlendSrf` `Circle` `ClearClippingSections`
`CloseCrv` `ContinueCurve` `ContinueInterpCrv` `CreateUVCrv` `Crv2View` `CrvDeviation`
`CrvEnd` `CrvSeam` `CrvStart` `Curve` `CurveBoolean` `CurveThroughPolyline`
`CurveThroughPt` `CurveThroughSrfControlPt` `DeleteSubCrv` `DevLoft` `DigLine` `DimCurveLength`
`EdgeSrf` `Ellipse` `ExtendCrvOnSrf` `ExtractIsocurve` `ExtractLineTypeSegments` `ExtractPipedCurve`
`ExtractSubCrv` `ExtrudeCrv` `ExtrudeCrvAlongCrv` `ExtrudeCrvTapered` `ExtrudeCrvToPoint` `ExtrudeMesh`
`ExtrudeSrf` `ExtrudeSrfAlongCrv` `ExtrudeSrfTapered` `ExtrudeSrfToPoint` `ExtrudeSubD` `FilletSrfCrv`
`FitCrv` `FitCurveToSurface` `FixedLengthCrvEdit` `HandleCurve` `Helix` `InflateCrv`
`InsertLineIntoCrv` `InterpCrv` `InterpCrvOnSrf` `Line` `LineThroughPt` `LinearLight`
`Lines` `LinetypeDisplay` `LinetypeWithShapes` `Linetypes` `Loft` `LoftSubD`
`MarkupCircle` `MarkupPolyline` `MatchCrvDir` `MatchSrf` `MergeCrv` `MeshFromLines`
`MeshOutline` `MeshPatch` `MeshPolyline` `MoveCrv` `MoveExtractedIsocurve` `NetworkSrf`
`OffsetCrvOnSrf` `OrientCrvToEdge` `OrientOnCrv` `Patch` `PatchSingleFace` `PlanarSrf`
`Polyline` `PolylineOnMesh` `RailRevolve` `RebuildCrvNonUniform` `ReducePolyline` `RenderArctic`
`Revolve` `RevolvedHole` `RhombicSpirallohedron` `SelClosedCrv` `SelCrv` `SelDimLinear`
`SelLine` `SelLinetype` `SelOpenCrv` `SelPlanarCrv` `SelPlanarSrf` `SelPolyline`
`SelSelfIntersectingCrv` `SelShortCrv` `SelSubDCrv` `SetCustomLinetype` `SetLayerLinetype` `SetLinetype`
`SetLinetypeScale` `SimplifyCrv` `SoftEditCrv` `Spiral` `SplitMeshWithCurve` `StretchCrv`
`SubCrv` `Super_Sweep` `Sweep1` `Sweep1SubD` `Sweep2` `Sweep2SubD`
`ToNurbsCrv` `ToSubDCrv` `TweenCurves` `VariableBlendSrf`

### 网格 Mesh（97）

`AddNgonsToMesh` `ApplyMesh` `ApplyMeshUVN` `ClearAllMeshes` `ClearAnalysisMeshes` `CollapseMeshEdge`
`CollapseMeshFace` `CollapseMeshFacesByArea` `CollapseMeshFacesByAspectRatio` `CollapseMeshFacesByEdgeLength` `CollapseMeshVertex` `CullDegenerateMeshFaces`
`DeleteMeshNgons` `DupMeshEdge` `DupMeshHoleBoundary` `ExtractAnalysisMesh` `ExtractConnectedMeshFaces` `ExtractDuplicateMeshFaces`
`ExtractMeshEdges` `ExtractMeshFaces` `ExtractMeshFacesByArea` `ExtractMeshFacesByAspectRatio` `ExtractMeshFacesByDraftAngle` `ExtractMeshFacesByEdgeLength`
`ExtractMeshPart` `ExtractNonManifoldMeshEdges` `ExtractRenderMesh` `ExtractUVMesh` `ExtrudeMesh` `FillMeshHole`
`FillMeshHoles` `HideRenderMesh` `MatchMeshEdge` `Merge2MeshFaces` `Mesh` `MeshBooleanDifference`
`MeshBooleanIntersection` `MeshBooleanSplit` `MeshBooleanUnion` `MeshBox` `MeshCone` `MeshCylinder`
`MeshDiffuseSphere` `MeshEllipsoid` `MeshFibonacciSphere` `MeshFromLines` `MeshFromPoints` `MeshIcoSphere`
`MeshIntersect` `MeshOutline` `MeshPatch` `MeshPlane` `MeshPolyline` `MeshQuadSphere`
`MeshRepair` `MeshSelfIntersect` `MeshSelfSplit` `MeshSphere` `MeshSplit` `MeshSplitNon2Manifolds`
`MeshToNURB` `MeshTorus` `MeshTriangleSphere` `MeshTrim` `MeshTruncatedCone` `OffsetMesh`
`PlanarMesh` `PolylineOnMesh` `QuadRemesh` `QuadrangulateMesh` `RebuildMesh` `RebuildMeshNormals`
`ReduceMesh` `SelClosedMesh` `SelConnectedMeshFaces` `SelMesh` `SelMeshEdges` `SelMeshFacesByArea`
`SelMeshFacesByAspectRatio` `SelMeshFacesByDraftAngle` `SelMeshFacesByEdgeLength` `SelMeshPart` `SelNakedMeshEdgePt` `SelOpenMesh`
`SetMeshSurfaceParameters` `ShowRenderMesh` `SnapToMeshObject` `SnapToMeshes` `SplitDisjointMesh` `SplitMeshEdge`
`SplitMeshWithCurve` `SubDFromMesh` `SwapMeshEdge` `ToggleRenderMesh` `TriangulateMesh` `TriangulateRenderMeshes`
`UnifyMeshNormals`

### SubD（31）

`CreaseSubDEdge` `ExpandSubDEdges` `ExtrudeSubD` `LoftSubD` `MatchSubD` `OffsetSubD`
`PackSubDFaces` `RepairSubD` `SelClosedSubD` `SelOpenSubD` `SelSubD` `SelSubDCrv`
`SelSubDEdges` `SnapToSubDObject` `SpinSubDEdge` `SubDBox` `SubDCone` `SubDCylinder`
`SubDEllipsoid` `SubDFromMesh` `SubDPlane` `SubDSphere` `SubDTorus` `SubDTruncatedCone`
`Subdivide` `Sweep1SubD` `Sweep2SubD` `ToSubD` `ToSubDCrv` `ToggleSubDDisplay`
`ToggleSubDFaceEdgeVertex`

### 选择 / 框选 / 子对象（141）

`ClearUndoSelection` `DatumPlanePick` `FWSelect` `IntersectSelf` `MeshSelfIntersect` `MeshSelfSplit`
`MicroScribeSelectTip` `NamedSelections` `PtOffSelected` `RedoSelection` `SelAll` `SelAnnotationStyle`
`SelBadObjects` `SelBaked` `SelBlockInstance` `SelBlockInstanceNamed` `SelBoundary` `SelBox`
`SelBrush` `SelBrushPoints` `SelCaptives` `SelChain` `SelChildren` `SelCircular`
`SelClippingPlane` `SelClippingPlaneInViewport` `SelClosedCrv` `SelClosedMesh` `SelClosedPolysrf` `SelClosedSrf`
`SelClosedSubD` `SelColor` `SelConnected` `SelConnectedMeshFaces` `SelControlPoint` `SelControlPointRegion`
`SelControls` `SelCrossing` `SelCrv` `SelDetail` `SelDim` `SelDimAngular`
`SelDimCentermark` `SelDimLinear` `SelDimOrdinate` `SelDimOverride` `SelDimRadial` `SelDimTextOverride`
`SelDot` `SelDup` `SelDupAll` `SelEdgeLoop` `SelEdgeRing` `SelExtrusion`
`SelFaceLoop` `SelFacesToBoundary` `SelFence` `SelFontUse` `SelGroup` `SelHatch`
`SelHatchPattern` `SelID` `SelIsolated` `SelKey` `SelKeyValue` `SelLast`
`SelLayer` `SelLayerNumber` `SelLeader` `SelLight` `SelLine` `SelLinetype`
`SelMappingWidget` `SelMaterialName` `SelMesh` `SelMeshEdges` `SelMeshFacesByArea` `SelMeshFacesByAspectRatio`
`SelMeshFacesByDraftAngle` `SelMeshFacesByEdgeLength` `SelMeshPart` `SelMirroredBlocks` `SelNakedMeshEdgePt` `SelName`
`SelNamedViewWidget` `SelNonManifold` `SelNone` `SelObjectsWithBrokenHistory` `SelObjectsWithHistory` `SelOpenCrv`
`SelOpenMesh` `SelOpenPolysrf` `SelOpenSrf` `SelOpenSubD` `SelOrphanDrawings` `SelParents`
`SelPicture` `SelPlanarCrv` `SelPlanarSrf` `SelPolyline` `SelPolysrf` `SelPrev`
`SelPt` `SelPtCloud` `SelRectangular` `SelRenderColor` `SelSelfIntersectingCrv` `SelShortCrv`
`SelSmall` `SelSrf` `SelSubD` `SelSubDCrv` `SelSubDEdges` `SelText`
`SelTrimmedSrf` `SelU` `SelUV` `SelUntrimmedSrf` `SelV` `SelValue`
`SelVisible` `SelVolumeObject` `SelVolumePipe` `SelVolumeSphere` `SelWindow` `Select`
`SelectFacesByNormal` `SelectionFilter` `SelectionFilterEdges` `SelectionFilterEnable` `SelectionFilterFaces` `SelectionFilterNone`
`SelectionFilterToggle` `SelectionFilterVertices` `ShadeSelected` `ShowSelected` `ShowSelectedInDetail` `ShowSelectedInViewport`
`UndoSelected` `UndoSelection` `UnlockSelected`

### 显示 / 渲染 / 视图（142）

`3View` `4View` `AliasStyleLight` `BackgroundBitmap` `BatchRenderNamedViews` `BringViewportToTop`
`Camera` `ChangeLightType` `ClearAllObjectDisplayModes` `CloseRenderWindow` `CloseViewport` `ConvertToSingleSpans`
`CopyDetailToViewport` `CopyRenderWindowToClipboard` `CopyViewportToDetail` `Crv2View` `DatumPlaneNormalView` `DatumPlaneNormalViewClose`
`DigCamera` `DirectionalLight` `DisplayCommandPrompt` `DisplayProperties` `DollyZoom` `DupAnnotationStyle`
`EditLightByHighlight` `EditLightByLooking` `Environments` `ExpandSubDEdges` `ExportRenderSettings` `ExtractIsocurve`
`ExtractRenderMesh` `ExtractWireframe` `FW2Panel` `FWCancelPanel` `FWHighlight` `FWPanel`
`FlatShade` `HideInViewports` `HideRenderMesh` `HighlightObjectLayers` `ImportRenderSettings` `IsolateInViewports`
`KeyShotRender` `Lights` `LinearLight` `LinetypeDisplay` `LockViewport` `MaxViewport`
`MoveExtractedIsocurve` `NamedView` `NewFloatingViewport` `NewViewport` `NextOrthoViewport` `NextPerspectiveViewport`
`NextViewport` `NextViewportToTop` `OneView` `OrientCameraToSrf` `Pan` `PointLight`
`PrevViewport` `Print` `PrintDisplay` `PushViewportToBack` `ReadViewportsFromFile` `RectangularLight`
`RedoView` `RefreshShade` `Render` `RenderArctic` `RenderAssignMaterialToLayer` `RenderAssignMaterialToLayersOfObjects`
`RenderAssignMaterialToObjects` `RenderBlowup` `RenderInWindow` `RenderMergeIdenticalMaterials` `RenderOpenLastRendering` `RenderOpenRenderImage`
`RenderPreview` `RenderPreviewInWindow` `RenderPreviewWindow` `RenderWindow` `Rendering` `RotateCamera`
`RotateView` `SaveClippingSectionViews` `SaveRenderWindowAs` `ScreenCaptureToClipboard` `ScreenCaptureToFile` `SelClippingPlaneInViewport`
`SelLight` `SelNamedViewWidget` `SelRenderColor` `SetActiveViewport` `SetCurrentRenderPlugIn` `SetDisplayMode`
`SetMaximizedViewport` `SetObjectDisplayMode` `SetSpotlightToView` `SetView` `SetViewToSpotlight` `SetZoomExtentsBorder`
`Shade` `ShadeSelected` `ShowInViewports` `ShowRenderMesh` `ShowSelectedInViewport` `Snapshots`
`SplitViewportHorizontal` `SplitViewportVertical` `Spotlight` `SunLight` `SwapView` `SynchronizeRenderColors`
`SynchronizeViews` `TiltView` `ToggleFloatingViewport` `ToggleLockedActiveRealtimeViewport` `TogglePausedActiveRealtimeViewport` `ToggleRenderMesh`
`ToggleSubDDisplay` `TriangulateRenderMeshes` `UndoView` `UnisolateInViewports` `ViewCaptureToClipboard` `ViewCaptureToFile`
`ViewClippingSections` `ViewFirstFrame` `ViewFrameNumber` `ViewLastFrame` `ViewNextFrame` `ViewPreviousFrame`
`ViewportProperties` `ViewportTabs` `Zoom` `Zoom1To1Calibrate` `ZoomClippingDrawings` `ZoomEnds`
`ZoomLens` `ZoomNaked` `ZoomNonManifold` `ZoomZeroToOne`

### 工作平面 / 坐标 / 捕捉（54）

`ApplyPlanarMapping` `AutoAlignCPlane` `CPlane` `CopyCPlaneSettingsToAll` `CopyCPlaneToAll` `DisableOsnap`
`Grid` `Gumball` `GumballAlignment` `GumballAutoReset` `GumballDynamicRelocate` `GumballMarkOrigin`
`GumballRelocate` `GumballReset` `GumballScaleMode` `GumballSettings` `MergeAllCoplanarFaces` `MergeCoplanarFace`
`NamedCPlane` `NextOrthoViewport` `Ortho` `OrthoAngle` `OrthoSnapToCPlaneZ` `Osnap`
`Planar` `PlanarDifference` `PlanarIntersection` `PlanarMesh` `PlanarSrf` `PlanarUnion`
`PointGrid` `ProjectOsnap` `ProjectToCPlane` `RemapCPlane` `SaveClippingSectionCPlanes` `SelPlanarCrv`
`SelPlanarSrf` `SetOrtho` `SetPlanar` `SetSnap` `ShowOsnap` `Snap`
`SnapSize` `SnapToLocked` `SnapToMeshObject` `SnapToMeshes` `SnapToOccluded` `SnapToSubDObject`
`Snapshots` `SplitViewportHorizontal` `SrfControlPtGrid` `SrfPtGrid` `SynchronizeCPlanes` `TriangulateNonPlanarQuads`

### 图层 / 属性 / 对象管理（156）

`AddMissingBlockAttributeKeys` `AddObjectsToBlock` `AddToGroup` `BatchRenderNamedViews` `Block` `BlockContent`
`BlockEdit` `BlockManager` `BlockResetScale` `Boolean2Objects` `ChangeLayer` `ChangeToCurrentLayer`
`CheckNewObjects` `ClearAllObjectDisplayModes` `ClippingPlaneProperties` `CloseTagManager` `ComputeVertexColors` `ConvertTextToBlockAttribute`
`CopyLinkedBlockDefinition` `CopyToLayer` `CreateUniqueBlock` `DatumPlaneLock` `DeleteTag` `DisplayProperties`
`DocumentProperties` `DocumentPropertiesPage` `DupLayer` `EditHatchGradient` `ExplodeBlock` `ExportBlockAttributes`
`ExportLinkedBlocks` `ExtractCustomMappingObject` `ExtractLineTypeSegments` `GH2ShowBakeData` `GrasshopperPlayer` `Group`
`Hatch` `HatchBase` `HatchPattern` `HatchScale` `Hide` `HideInDetail`
`HideInViewports` `HideLayersInDetail` `HidePt` `HideRenderMesh` `HideSwap` `HighlightObjectLayers`
`InvertSubObjects` `Isolate` `IsolateInViewports` `IsolateLock` `Layer` `LayerBook`
`LayerStateManager` `LayoutProperties` `LinetypeDisplay` `LinetypeWithShapes` `Linetypes` `Lock`
`LockSwap` `LockViewport` `MatchLayer` `MatchProperties` `Materials` `MoveTargetToObjects`
`NamedCPlane` `NamedPosition` `NamedSelections` `NamedView` `OneLayerOff` `OneLayerOn`
`PasteAsBlock` `Properties` `PropertiesPage` `PurgeRefObjects` `RemoveFromGroup` `RemovePerFaceColors`
`RenderAssignMaterialToLayer` `RenderAssignMaterialToLayersOfObjects` `RenderAssignMaterialToObjects` `RenderMergeIdenticalMaterials` `ReplaceBlock` `RescueBlockOrphans`
`SaveCurrentTagFilter` `SelBadObjects` `SelBlockInstance` `SelBlockInstanceNamed` `SelColor` `SelGroup`
`SelHatch` `SelHatchPattern` `SelIsolated` `SelLayer` `SelLayerNumber` `SelLinetype`
`SelMaterialName` `SelMirroredBlocks` `SelName` `SelNamedViewWidget` `SelObjectsWithBrokenHistory` `SelObjectsWithHistory`
`SelRenderColor` `SelVolumeObject` `SetCustomLinetype` `SetDimensionLayer` `SetGroupName` `SetHatchBaseAndRotation`
`SetIgesLayerLevelMap` `SetLayerLinetype` `SetLayerToObject` `SetLinetype` `SetLinetypeScale` `SetObjectDisplayMode`
`SetObjectName` `SetPerFaceColorByFacePack` `Show` `ShowDir` `ShowDirOff` `ShowEdges`
`ShowEdgesOff` `ShowEnds` `ShowEndsOff` `ShowInDetail` `ShowInViewports` `ShowLayersInDetail`
`ShowOsnap` `ShowPt` `ShowRenderMesh` `ShowSelected` `ShowSelectedInDetail` `ShowSelectedInViewport`
`ShowToolBar` `ShowZBuffer` `SnapToLocked` `SnapToMeshObject` `SnapToSubDObject` `SynchronizeRenderColors`
`Tag` `TagFilter` `TagManager` `TagsFromLayers` `TextObject` `TextProperties`
`ToggleLockedActiveRealtimeViewport` `ToolbarLock` `Ungroup` `UngroupAll` `Unisolate` `UnisolateInViewports`
`UnisolateLock` `Unlock` `UnlockSelected` `UserInterfaceObjectProxy` `ViewportProperties` `Weight`

### 标注 / 文字 / 出图（107）

`AlignClippingDrawings` `AssignBlankTexture` `BooleanIntersection` `ClearClippingSections` `ClippingDrawings` `ClippingPlane`
`ClippingPlaneProperties` `ClippingSections` `ConvertExtrusion` `ConvertTextToBlockAttribute` `CopyDetailToViewport` `CopyLayout`
`CopyViewportToDetail` `CreateClippingDrawingTemplate` `Detail` `DigSection` `Dim` `DimAligned`
`DimAngle` `DimArea` `DimCreaseAngle` `DimCurveLength` `DimDiameter` `DimOrdinate`
`DimRadius` `DimRecenterText` `DimRotated` `DimUserText` `DimVolume` `DisableClippingPlane`
`DocumentText` `DownloadLibraryTextures` `DupAnnotationStyle` `EditClippingDrawings` `EnableClippingPlane` `ExplodeText`
`ExportLayout` `ExtractClippingSections` `ExtractClippingSlices` `FindText` `GetDocumentUserText` `GetUserText`
`HideInDetail` `HideLayersInDetail` `ImportAnnotationStyles` `ImportLayout` `JoinText` `Layout`
`LayoutProperties` `Layouts` `Leader` `MarkupDim` `MarkupLeader` `MarkupText`
`MatchAnnotation` `MeshBooleanIntersection` `NestedClippingDrawing` `NextDetail` `Notes` `PackTextures`
`PlanarIntersection` `PointCloudSection` `PrevDetail` `PurgeOrphanDrawings` `QuickText` `RLeaderEdit`
`RTextEdit` `RefreshAllTextures` `SaveClippingSectionCPlanes` `SaveClippingSectionViews` `SaveWindowLayout` `ScaleTextHeight`
`Section` `SectionBox` `SelAnnotationStyle` `SelClippingPlane` `SelClippingPlaneInViewport` `SelDetail`
`SelDim` `SelDimAngular` `SelDimCentermark` `SelDimLinear` `SelDimOrdinate` `SelDimOverride`
`SelDimRadial` `SelDimTextOverride` `SelLeader` `SelOrphanDrawings` `SelText` `SetCurrentAnnotationStyle`
`SetDetailBorder` `SetDetailScale` `SetDimensionLayer` `SetDocumentUserText` `SetUserText` `ShowInDetail`
`ShowLayersInDetail` `ShowSelectedInDetail` `Text` `TextObject` `TextProperties` `Textures`
`UnpackTextures` `UpdateClippingDrawings` `ViewClippingSections` `WindowLayout` `ZoomClippingDrawings`

### 文件 / 导入导出 / 模板（92）

`AlignProfiles` `AttachGHSData` `Audit` `Audit3dmFile` `Autosave` `CheckNewObjects`
`CloseCrv` `CloseRenderWindow` `CloseTagManager` `CloseViewport` `ClosestPt` `CreateClippingDrawingTemplate`
`DatumPlaneNormalViewClose` `DatumPlaneSave` `Export` `ExportBitmaps` `ExportBlockAttributes` `ExportLayout`
`ExportLinkedBlocks` `ExportNavisworks` `ExportRenderSettings` `ExportRuiFile` `ExportWithOrigin` `FaroSetLogFile`
`FileExplorer` `GH2DocsExport` `GH2ExamineFile` `GH2ExportIcons` `GH2FileDifference` `HistoryPurge`
`IgesImportOptions` `Import` `ImportAnnotationStyles` `ImportGuides` `ImportLayout` `ImportMarkup`
`ImportRenderSettings` `IncrementalSave` `Insert` `InsertControlPoint` `InsertEdge` `InsertEditPoint`
`InsertKink` `InsertKnot` `InsertLineIntoCrv` `InsertPoint` `KeyShotExport` `New`
`NewFloatingViewport` `NewFromTemplate` `NewViewport` `Open` `OpenRecent` `OpenURL`
`OptionsExport` `OptionsImport` `PackSubDFaces` `PackTextures` `PackageManager` `Purge`
`PurgeOrphanDrawings` `PurgeRefObjects` `ReadCommandFile` `ReadViewportsFromFile` `RenderOpenLastRendering` `RenderOpenRenderImage`
`Rescue3dmFile` `Save` `SaveACopy` `SaveAs` `SaveAsTemplate` `SaveClippingSectionCPlanes`
`SaveClippingSectionViews` `SaveCurrentTagFilter` `SaveRenderWindowAs` `SaveSmall` `SaveWindowLayout` `ScreenCaptureToFile`
`SelClosedCrv` `SelClosedMesh` `SelClosedPolysrf` `SelClosedSrf` `SelClosedSubD` `SelOpenCrv`
`SelOpenMesh` `SelOpenPolysrf` `SelOpenSrf` `SelOpenSubD` `SetPerFaceColorByFacePack` `UnpackTextures`
`ViewCaptureToFile` `Worksession`

### 分析 / 检测 / 测量（57）

`Angle` `ApplySurfaceMapping` `Area` `AreaCentroid` `AreaMoments` `BakeMapping`
`Check` `CheckInLicense` `CheckNewObjects` `CheckOutLicense` `ClearAnalysisMeshes` `CollapseMeshFacesByArea`
`Curvature` `CurvatureAnalysis` `CurvatureAnalysisOff` `CurvatureGraph` `CurvatureGraphOff` `CutVolume`
`DimAngle` `DimArea` `DimCreaseAngle` `DimVolume` `DirectionalLight` `Distance`
`DraftAngleAnalysis` `DraftAngleAnalysisOff` `DraftAnglePoint` `EMap` `EMapOff` `EdgeContinuity`
`EvaluatePt` `EvaluateUVPt` `ExtractAnalysisMesh` `ExtractCurvatureGraph` `ExtractMeshFacesByArea` `ExtractMeshFacesByDraftAngle`
`GlobalEdgeContinuity` `MarkupRectangle` `MeshTriangleSphere` `OrthoAngle` `PerspectiveAngle` `Rectangle`
`RemapCPlane` `RemoveMappingChannel` `SelBadObjects` `SelMeshFacesByArea` `SelMeshFacesByDraftAngle` `SelVolumeObject`
`SelVolumePipe` `SelVolumeSphere` `ThicknessAnalysis` `ThicknessAnalysisOff` `Volume` `VolumeCentroid`
`VolumeMoments` `Zebra` `ZebraOff`

### 变换 / 阵列 / 定位（98）

`Align` `AlignClippingDrawings` `AlignProfiles` `AlignVertices` `Array` `ArrayCrv`
`ArrayCrvOld` `ArrayCrvOnSrf` `ArrayHole` `ArrayHolePolar` `ArrayLinear` `ArrayPolar`
`ArraySrf` `AutoAlignCPlane` `BlockResetScale` `Copy` `CopyCPlaneSettingsToAll` `CopyCPlaneToAll`
`CopyDetailToViewport` `CopyHole` `CopyLayout` `CopyLinkedBlockDefinition` `CopyRenderWindowToClipboard` `CopyToClipboard`
`CopyToClipboardAt` `CopyToLayer` `CopyViewportToDetail` `DigScale` `DimAligned` `DimRotated`
`Distribute` `DragCopy` `FlattenSrf` `GumballAlignment` `GumballScaleMode` `HatchScale`
`JoinCopy` `MatchUvScale` `Mirror` `MirrorHole` `Move` `MoveCrv`
`MoveEdge` `MoveExtractedIsocurve` `MoveFace` `MoveHole` `MoveTargetToObjects` `MoveUVN`
`MoveUntrimmedEdge` `MoveUntrimmedFace` `NamedPosition` `Orient` `Orient3Pt` `OrientCameraToSrf`
`OrientCrvToEdge` `OrientOnCrv` `OrientOnSrf` `Project` `ProjectOsnap` `ProjectToCPlane`
`Pull` `PushPull` `RemapCPlane` `RememberCopyOptions` `RemoveAllNakedMicroEdges` `RemoveControlPoint`
`RemoveCrease` `RemoveFromGroup` `RemoveGuide` `RemoveKnot` `RemoveMappingChannel` `RemoveMultiKnot`
`RemovePerFaceColors` `RemoveSymmetry` `Rotate` `Rotate3D` `RotateCamera` `RotateHole`
`RotateView` `SaveACopy` `Scale` `Scale1D` `Scale2D` `ScaleByPlane`
`ScaleEach` `ScaleNU` `ScalePositions` `ScaleTextHeight` `SelDimOverride` `SelMirroredBlocks`
`SetDetailScale` `SetLinetypeScale` `SetPt` `Shear` `Smash` `SoftMove`
`UnrollSrf` `UnrollSrfUV`

### 历史 / 撤销 / 命令层（40）

`AliasStyle` `AliasStyleDark` `AliasStyleLight` `AliasStyleRestore` `Cancel` `ClearUndo`
`ClearUndoSelection` `CommandHelp` `CommandHistory` `CommandList` `CommandMode` `CommandPrompt`
`Commands` `DisplayCommandPrompt` `Exit` `FWCancel` `FWCancelPanel` `History`
`HistoryPurge` `HistoryUpdate` `MacroEditor` `Macros` `ReadCommandFile` `Redo`
`RedoMultiple` `RedoSelection` `RedoView` `RenderOpenLastRendering` `Repeat` `RunScript`
`SelLast` `SelObjectsWithBrokenHistory` `SelObjectsWithHistory` `ToggleInstantAliases` `Undo` `UndoMultiple`
`UndoSelected` `UndoSelection` `UndoView` `ViewLastFrame`

### 面板 / 工具栏 / 选项 / UI（26）

`CommandPrompt` `DisplayCommandPrompt` `DocumentProperties` `DocumentPropertiesPage` `ExportRuiFile` `FW2Panel`
`FWCancelPanel` `FWPanel` `FWStatus` `GH2ExportIcons` `GH2IconSetup` `GH2IconSymbol`
`IgesImportOptions` `MCPStatus` `Options` `OptionsExport` `OptionsImport` `OptionsMigrate`
`OptionsPage` `PopupMenu` `PopupPopular` `PopupToolbar` `RememberCopyOptions` `ShowToolBar`
`Toolbar` `ToolbarLock`

### Grasshopper / 脚本 / 开发（56）

`AliasStyleLight` `AttachGHSData` `ChangeLightType` `CurveThroughPolyline` `CurveThroughPt` `CurveThroughSrfControlPt`
`DirectionalLight` `DupLayer` `EditLightByHighlight` `EditLightByLooking` `EditScript` `FWHighlight`
`GH2` `GH2Banner` `GH2Docs` `GH2DocsAuthoring` `GH2DocsExport` `GH2ExamineFile`
`GH2ExportIcons` `GH2FileDifference` `GH2IconSetup` `GH2IconSymbol` `GH2Log` `GH2Plugins`
`GH2ShowBakeData` `GH2WipeBakeData` `Grasshopper` `GrasshopperDeveloperSettings` `GrasshopperFolders` `GrasshopperGetSDKDocumentation`
`GrasshopperIgnorePlugin` `GrasshopperLoadOneByOne` `GrasshopperPlayer` `GrasshopperPluginList` `Heightfield` `HighlightObjectLayers`
`Lights` `LineThroughPt` `LinearLight` `LoadScript` `PlaneThroughPt` `PointLight`
`RectangularLight` `RunPythonScript` `RunScript` `ScaleTextHeight` `ScriptEditor` `SelLight`
`SetFlythroughAnimation` `SetSpotlightToView` `SetViewToSpotlight` `Spotlight` `StartScriptServer` `SunLight`
`ToggleRightSidebar` `Weight`

### 我们的插件 FW*（21）

`FW` `FW2` `FW2Panel` `FW2Recognize` `FW2Restore` `FWCancel`
`FWCancelPanel` `FWClear` `FWEvidence` `FWFocus` `FWHighlight` `FWList`
`FWPanel` `FWRebuild` `FWRecognize` `FWRepair` `FWSelect` `FWStatus`
`FWSuppress` `FWTest` `FeatureWorks`

### 未归入任何域（296）

`3DFace` `AI` `About` `AboutRhino` `AcadSchemes` `AddGuide`
`AddNextU` `AddNextV` `AddPrevU` `AddPrevV` `Alerter` `AppendFace`
`ApplyBoxMapping` `ApplyCustomMapping` `ApplyCylindricalMapping` `ApplyOcsMapping` `ApplySphericalMapping` `Arrowhead`
`Bake` `BatchMode` `Bevel` `BevelGearSrf` `Boss` `Bounce`
`BoundingBox` `Box` `BoxEdit` `Bridge` `BringForward` `BringToFront`
`CSec` `Cage` `CageEdit` `Calc` `CalcRPN` `Catenary`
`Centermark` `ChangeDegree` `ChangeSpace` `Clash` `ClearDrawOrder` `Cone`
`Conic` `Connect` `ConnectSrf` `Containers` `Contour` `Convert`
`ConvertDots` `ConvertToBeziers` `Conway` `CreateRegions` `CullControlPolygon` `Cut`
`CutAt` `CutPlane` `Cylinder` `DatumPlane` `DatumPlaneRecall` `DatumPlaneRestore`
`Decal` `DecalWidgetOff` `DecimalPoint` `Delete` `Diameter` `DigBeep`
`DigCalibrate` `DigClick` `DigDisconnect` `DigPause` `DigSketch` `Digitize`
`Dir` `Divide` `Domain` `Dome` `Dot` `DragMode`
`DragStrength` `Drape` `DrapePt` `DupBorder` `DupEdge` `EarthAnchorPoint`
`Echo` `EditPtOn` `Ellipsoid` `Elmo` `EndBulge` `EndUVEditor`
`Enter` `EnterEnd` `Extend` `ExtendDynamic` `ExtendSrf` `ExtractBadSrf`
`ExtractControlPolygon` `ExtractPt` `Fair` `FaroDiagnostics` `FaroHardwareConfig` `FaroProbes`
`FaroTemperature` `Fill` `Fin` `FitSrf` `Flip` `FoldFace`
`Fullscreen` `GCon` `GeometricTolerance` `GetIssueState` `GroundPlane` `HBar`
`HelicalGearSrf` `Help` `Hydrostatics` `Hyperbola` `Hyperlink` `IGESStudy`
`IPlane` `Inset` `Inspect` `Intersect` `IntersectTwoSets` `Invert`
`InvertPt` `InvoluteGear` `Isometric` `JZ` `KeyShotSettings` `KeyShotUpdate`
`Knife` `Lasso` `LegacyRecordAnimation` `Length` `Libraries` `LimitReferenceModel`
`List` `Login` `Logout` `MCPConnect` `MCPStart` `MPlane`
`Maelstrom` `Make2D` `MakeNonPeriodic` `MakePeriodic` `MakeUniform` `MakeUniformUV`
`MappingWidget` `MappingWidgetOff` `MarkFoci` `Markup` `MarkupEraser` `MarkupPicture`
`MarkupSketch` `Match` `MatchMapping` `Maximize` `Menus` `MergeAllEdges`
`MergeEdge` `MigratePlugIns` `Minimize` `MissingAssets` `ModelBasepoint` `ModifyRadius`
`MultiPause` `MultiPipe` `NextU` `NextV` `NoEcho` `NonmanifoldMerge`
`Notifications` `Overlap` `Parabola` `Parabola3Pt` `Paraboloid` `Paste`
`PasteAt` `Pause` `PerspectiveMatch` `Picture` `Pipe` `Plan`
`Plane` `PlayAnimation` `Point` `PointCloud` `PointCloudContour` `PointDeviation`
`Points` `PointsFromUV` `PointsOff` `PointsOn` `PolarZonohedron` `Polygon`
`PolygonCount` `Polyhedron` `PrevU` `PrevV` `Pyramid` `QuickHull`
`Rack` `Radiate` `RadiateFind` `Radius` `ReadEveryIGESEntity` `Rebuild`
`RebuildOld` `RebuildUV` `RecordAnimation` `ReducePointCloud` `Reflect` `ReleaseFromCage`
`Reparameterize` `ReportProblem` `Reset` `ResetMessageBoxes` `Restore` `RevCloud`
`Revert` `RhinoCyclesReport` `Run` `STEPTree` `SendBackward` `SendToBack`
`SetDotNetRuntime` `SetOneDaySunAnimation` `SetPathAnimation` `SetRedrawOff` `SetRedrawOn` `SetSeasonalSunAnimation`
`SetSurfaceTangent` `SetTurntableAnimation` `SetWorkingFolder` `SetWorldOrigin` `ShortPath` `ShrinkWrap`
`Silhouette` `Sketch` `Slab` `Slide` `SmartTrack` `Smooth`
`SoftEditSrf` `SoftTransform` `SpaceMouse` `Sphere` `SphereTangentToThreeSurfaces` `Split`
`SplitEdge` `SplitPointCloud` `SplitRefitSurface` `Splop` `Squish` `SquishBack`
`SquishInfo` `SrfPt` `SrfSeam` `StepUnitsAndTolerance` `Stitch` `Stretch`
`Sun` `SymbolContent` `Symmetry` `SystemInfo` `ToExtrusion` `ToNURBS`
`ToggleGpuProcedurals` `ToggleLeftSidebar` `Torus` `TruncatedCone` `TruncatedPyramid` `Tube`
`Turntable` `Tutorials` `TweenSurfaces` `UVEditor` `Unweld` `UnweldEdge`
`UnweldVertex` `Unwrap` `UseExtrusions` `Vectorize` `WalkAbout` `Waterman`
`WebBrowser` `Weld` `WeldEdge` `WeldVertices` `What` `XNurbs`
`XNurbsHelp` `基准面`

## 2. 全量字母索引（1256 条，无遗漏）

### A（55）

`AI` `About` `AboutRhino` `AcadSchemes` `AddGuide` `AddMissingBlockAttributeKeys`
`AddNextU` `AddNextV` `AddNgonsToMesh` `AddObjectsToBlock` `AddPrevU` `AddPrevV`
`AddToGroup` `Alerter` `AliasStyle` `AliasStyleDark` `AliasStyleLight` `AliasStyleRestore`
`Align` `AlignClippingDrawings` `AlignProfiles` `AlignVertices` `Angle` `AppendFace`
`ApplyBoxMapping` `ApplyCrv` `ApplyCustomMapping` `ApplyCylindricalMapping` `ApplyMesh` `ApplyMeshUVN`
`ApplyOcsMapping` `ApplyPlanarMapping` `ApplySphericalMapping` `ApplySurfaceMapping` `Arc` `ArcBlend`
`Area` `AreaCentroid` `AreaMoments` `Array` `ArrayCrv` `ArrayCrvOld`
`ArrayCrvOnSrf` `ArrayHole` `ArrayHolePolar` `ArrayLinear` `ArrayPolar` `ArraySrf`
`Arrowhead` `AssignBlankTexture` `AttachGHSData` `Audit` `Audit3dmFile` `AutoAlignCPlane`
`Autosave`

### B（30）

`BackgroundBitmap` `Bake` `BakeMapping` `BatchMode` `BatchRenderNamedViews` `Bend`
`Bevel` `BevelGearSrf` `BlendCrv` `BlendEdge` `BlendSrf` `Block`
`BlockContent` `BlockEdit` `BlockManager` `BlockResetScale` `Boolean2Objects` `BooleanDifference`
`BooleanIntersection` `BooleanSplit` `BooleanUnion` `Boss` `Bounce` `BoundingBox`
`Box` `BoxEdit` `Bridge` `BringForward` `BringToFront` `BringViewportToTop`

### C（111）

`CPlane` `CSec` `Cage` `CageEdit` `Calc` `CalcRPN`
`Camera` `Cancel` `Cap` `Catenary` `Centermark` `Chamfer`
`ChamferEdge` `ChamferSrf` `ChangeDegree` `ChangeLayer` `ChangeLightType` `ChangeSpace`
`ChangeToCurrentLayer` `Check` `CheckInLicense` `CheckNewObjects` `CheckOutLicense` `Circle`
`Clash` `ClearAllMeshes` `ClearAllObjectDisplayModes` `ClearAnalysisMeshes` `ClearClippingSections` `ClearDrawOrder`
`ClearUndo` `ClearUndoSelection` `ClippingDrawings` `ClippingPlane` `ClippingPlaneProperties` `ClippingSections`
`CloseCrv` `CloseRenderWindow` `CloseTagManager` `CloseViewport` `ClosestPt` `CollapseMeshEdge`
`CollapseMeshFace` `CollapseMeshFacesByArea` `CollapseMeshFacesByAspectRatio` `CollapseMeshFacesByEdgeLength` `CollapseMeshVertex` `CommandHelp`
`CommandHistory` `CommandList` `CommandMode` `CommandPrompt` `Commands` `ComputeVertexColors`
`Cone` `Conic` `Connect` `ConnectSrf` `Containers` `ContinueCurve`
`ContinueInterpCrv` `Contour` `Convert` `ConvertDots` `ConvertExtrusion` `ConvertTextToBlockAttribute`
`ConvertToBeziers` `ConvertToSingleSpans` `Conway` `Copy` `CopyCPlaneSettingsToAll` `CopyCPlaneToAll`
`CopyDetailToViewport` `CopyHole` `CopyLayout` `CopyLinkedBlockDefinition` `CopyRenderWindowToClipboard` `CopyToClipboard`
`CopyToClipboardAt` `CopyToLayer` `CopyViewportToDetail` `Crease` `CreaseSplitting` `CreaseSubDEdge`
`CreateClippingDrawingTemplate` `CreateRegions` `CreateSolid` `CreateUVCrv` `CreateUniqueBlock` `Crv2View`
`CrvDeviation` `CrvEnd` `CrvSeam` `CrvStart` `CullControlPolygon` `CullDegenerateMeshFaces`
`Curvature` `CurvatureAnalysis` `CurvatureAnalysisOff` `CurvatureGraph` `CurvatureGraphOff` `Curve`
`CurveBoolean` `CurveThroughPolyline` `CurveThroughPt` `CurveThroughSrfControlPt` `Cut` `CutAt`
`CutPlane` `CutVolume` `Cylinder`

### D（76）

`DatumPlane` `DatumPlaneLock` `DatumPlaneNormalView` `DatumPlaneNormalViewClose` `DatumPlanePick` `DatumPlaneRecall`
`DatumPlaneRestore` `DatumPlaneSave` `Decal` `DecalWidgetOff` `DecimalPoint` `Delete`
`DeleteFaces` `DeleteMeshNgons` `DeleteSubCrv` `DeleteTag` `Detail` `DevLoft`
`Diameter` `DigBeep` `DigCalibrate` `DigCamera` `DigClick` `DigDisconnect`
`DigLine` `DigPause` `DigScale` `DigSection` `DigSketch` `Digitize`
`Dim` `DimAligned` `DimAngle` `DimArea` `DimCreaseAngle` `DimCurveLength`
`DimDiameter` `DimOrdinate` `DimRadius` `DimRecenterText` `DimRotated` `DimUserText`
`DimVolume` `Dir` `DirectionalLight` `DisableClippingPlane` `DisableOsnap` `DisplayCommandPrompt`
`DisplayProperties` `Distance` `Distribute` `Divide` `DivideAlongCreases` `DocumentProperties`
`DocumentPropertiesPage` `DocumentText` `DollyZoom` `Domain` `Dome` `Dot`
`DownloadLibraryTextures` `DraftAngleAnalysis` `DraftAngleAnalysisOff` `DraftAnglePoint` `DragCopy` `DragMode`
`DragStrength` `Drape` `DrapePt` `DupAnnotationStyle` `DupBorder` `DupEdge`
`DupFaceBorder` `DupLayer` `DupMeshEdge` `DupMeshHoleBoundary`

### E（78）

`EMap` `EMapOff` `EarthAnchorPoint` `Echo` `EdgeContinuity` `EdgeSrf`
`EditClippingDrawings` `EditHatchGradient` `EditLightByHighlight` `EditLightByLooking` `EditPtOn` `EditScript`
`Ellipse` `Ellipsoid` `Elmo` `EnableClippingPlane` `EndBulge` `EndUVEditor`
`Enter` `EnterEnd` `Environments` `EvaluatePt` `EvaluateUVPt` `Exit`
`ExpandSubDEdges` `Explode` `ExplodeBlock` `ExplodeText` `Export` `ExportBitmaps`
`ExportBlockAttributes` `ExportLayout` `ExportLinkedBlocks` `ExportNavisworks` `ExportRenderSettings` `ExportRuiFile`
`ExportWithOrigin` `Extend` `ExtendCrvOnSrf` `ExtendDynamic` `ExtendSrf` `ExtractAnalysisMesh`
`ExtractBadSrf` `ExtractClippingSections` `ExtractClippingSlices` `ExtractConnectedMeshFaces` `ExtractControlPolygon` `ExtractCurvatureGraph`
`ExtractCustomMappingObject` `ExtractDuplicateMeshFaces` `ExtractIsocurve` `ExtractLineTypeSegments` `ExtractMeshEdges` `ExtractMeshFaces`
`ExtractMeshFacesByArea` `ExtractMeshFacesByAspectRatio` `ExtractMeshFacesByDraftAngle` `ExtractMeshFacesByEdgeLength` `ExtractMeshPart` `ExtractNonManifoldMeshEdges`
`ExtractOriginalCaptives` `ExtractPipedCurve` `ExtractPt` `ExtractRenderMesh` `ExtractSrf` `ExtractSubCrv`
`ExtractUVMesh` `ExtractWireframe` `ExtrudeCrv` `ExtrudeCrvAlongCrv` `ExtrudeCrvTapered` `ExtrudeCrvToPoint`
`ExtrudeMesh` `ExtrudeSrf` `ExtrudeSrfAlongCrv` `ExtrudeSrfTapered` `ExtrudeSrfToPoint` `ExtrudeSubD`

### F（50）

`FW` `FW2` `FW2Panel` `FW2Recognize` `FW2Restore` `FWCancel`
`FWCancelPanel` `FWClear` `FWEvidence` `FWFocus` `FWHighlight` `FWList`
`FWPanel` `FWRebuild` `FWRecognize` `FWRepair` `FWSelect` `FWStatus`
`FWSuppress` `FWTest` `Fair` `FaroDiagnostics` `FaroHardwareConfig` `FaroProbes`
`FaroSetLogFile` `FaroTemperature` `FeatureWorks` `FileExplorer` `Fill` `FillMeshHole`
`FillMeshHoles` `Fillet` `FilletCorners` `FilletEdge` `FilletSrf` `FilletSrfCrv`
`FilletSrfToRail` `Fin` `FindText` `FitCrv` `FitCurveToSurface` `FitSrf`
`FixedLengthCrvEdit` `FlatShade` `FlattenSrf` `Flip` `Flow` `FlowAlongSrf`
`FoldFace` `Fullscreen`

### G（40）

`GCon` `GH2` `GH2Banner` `GH2Docs` `GH2DocsAuthoring` `GH2DocsExport`
`GH2ExamineFile` `GH2ExportIcons` `GH2FileDifference` `GH2IconSetup` `GH2IconSymbol` `GH2Log`
`GH2Plugins` `GH2ShowBakeData` `GH2WipeBakeData` `GeometricTolerance` `GetDocumentUserText` `GetIssueState`
`GetUserText` `GlobalEdgeContinuity` `Grasshopper` `GrasshopperDeveloperSettings` `GrasshopperFolders` `GrasshopperGetSDKDocumentation`
`GrasshopperIgnorePlugin` `GrasshopperLoadOneByOne` `GrasshopperPlayer` `GrasshopperPluginList` `Grid` `GroundPlane`
`Group` `Gumball` `GumballAlignment` `GumballAutoReset` `GumballDynamicRelocate` `GumballMarkOrigin`
`GumballRelocate` `GumballReset` `GumballScaleMode` `GumballSettings`

### H（24）

`HBar` `HandleCurve` `Hatch` `HatchBase` `HatchPattern` `HatchScale`
`Heightfield` `HelicalGearSrf` `Helix` `Help` `Hide` `HideInDetail`
`HideInViewports` `HideLayersInDetail` `HidePt` `HideRenderMesh` `HideSwap` `HighlightObjectLayers`
`History` `HistoryPurge` `HistoryUpdate` `Hydrostatics` `Hyperbola` `Hyperlink`

### I（34）

`IGESStudy` `IPlane` `IgesImportOptions` `Import` `ImportAnnotationStyles` `ImportGuides`
`ImportLayout` `ImportMarkup` `ImportRenderSettings` `IncrementalSave` `InflateCrv` `Insert`
`InsertControlPoint` `InsertEdge` `InsertEditPoint` `InsertKink` `InsertKnot` `InsertLineIntoCrv`
`InsertPoint` `Inset` `Inspect` `InterpCrv` `InterpCrvOnSrf` `Intersect`
`IntersectSelf` `IntersectTwoSets` `Invert` `InvertPt` `InvertSubObjects` `InvoluteGear`
`Isolate` `IsolateInViewports` `IsolateLock` `Isometric`

### J（5）

`JZ` `Join` `JoinCopy` `JoinEdge` `JoinText`

### K（5）

`KeyShotExport` `KeyShotRender` `KeyShotSettings` `KeyShotUpdate` `Knife`

### L（29）

`Lasso` `Layer` `LayerBook` `LayerStateManager` `Layout` `LayoutProperties`
`Layouts` `Leader` `LegacyRecordAnimation` `Length` `Libraries` `Lights`
`LimitReferenceModel` `Line` `LineThroughPt` `LinearLight` `Lines` `LinetypeDisplay`
`LinetypeWithShapes` `Linetypes` `List` `LoadScript` `Lock` `LockSwap`
`LockViewport` `Loft` `LoftSubD` `Login` `Logout`

### M（101）

`MCPConnect` `MCPStart` `MCPStatus` `MPlane` `MacroEditor` `Macros`
`Maelstrom` `Make2D` `MakeHole` `MakeNonPeriodic` `MakePeriodic` `MakeUniform`
`MakeUniformUV` `MappingWidget` `MappingWidgetOff` `MarkFoci` `Markup` `MarkupCircle`
`MarkupDim` `MarkupEraser` `MarkupLeader` `MarkupPicture` `MarkupPolyline` `MarkupRectangle`
`MarkupSketch` `MarkupText` `Match` `MatchAnnotation` `MatchCrvDir` `MatchLayer`
`MatchMapping` `MatchMeshEdge` `MatchProperties` `MatchSrf` `MatchSubD` `MatchUvScale`
`Materials` `MaxViewport` `Maximize` `Menus` `Merge2MeshFaces` `MergeAllCoplanarFaces`
`MergeAllEdges` `MergeCoplanarFace` `MergeCrv` `MergeEdge` `MergeFaces` `MergeSrf`
`Mesh` `MeshBooleanDifference` `MeshBooleanIntersection` `MeshBooleanSplit` `MeshBooleanUnion` `MeshBox`
`MeshCone` `MeshCylinder` `MeshDiffuseSphere` `MeshEllipsoid` `MeshFibonacciSphere` `MeshFromLines`
`MeshFromPoints` `MeshIcoSphere` `MeshIntersect` `MeshOutline` `MeshPatch` `MeshPlane`
`MeshPolyline` `MeshQuadSphere` `MeshRepair` `MeshSelfIntersect` `MeshSelfSplit` `MeshSphere`
`MeshSplit` `MeshSplitNon2Manifolds` `MeshToNURB` `MeshTorus` `MeshTriangleSphere` `MeshTrim`
`MeshTruncatedCone` `MicroScribeCalibrateTip` `MicroScribeDeviceInfo` `MicroScribeSelectTip` `MigratePlugIns` `Minimize`
`Mirror` `MirrorHole` `MissingAssets` `ModelBasepoint` `ModifyRadius` `Move`
`MoveCrv` `MoveEdge` `MoveExtractedIsocurve` `MoveFace` `MoveHole` `MoveTargetToObjects`
`MoveUVN` `MoveUntrimmedEdge` `MoveUntrimmedFace` `MultiPause` `MultiPipe`

### N（21）

`NamedCPlane` `NamedPosition` `NamedSelections` `NamedView` `NestedClippingDrawing` `NetworkSrf`
`New` `NewFloatingViewport` `NewFromTemplate` `NewViewport` `NextDetail` `NextOrthoViewport`
`NextPerspectiveViewport` `NextU` `NextV` `NextViewport` `NextViewportToTop` `NoEcho`
`NonmanifoldMerge` `Notes` `Notifications`

### O（29）

`Offset` `OffsetCrvOnSrf` `OffsetMesh` `OffsetMultiple` `OffsetNormal` `OffsetSrf`
`OffsetSubD` `OneLayerOff` `OneLayerOn` `OneView` `Open` `OpenRecent`
`OpenURL` `Options` `OptionsExport` `OptionsImport` `OptionsMigrate` `OptionsPage`
`Orient` `Orient3Pt` `OrientCameraToSrf` `OrientCrvToEdge` `OrientOnCrv` `OrientOnSrf`
`Ortho` `OrthoAngle` `OrthoSnapToCPlaneZ` `Osnap` `Overlap`

### P（67）

`PackSubDFaces` `PackTextures` `PackageManager` `Pan` `Parabola` `Parabola3Pt`
`Paraboloid` `Paste` `PasteAsBlock` `PasteAt` `Patch` `PatchSingleFace`
`Pause` `PerspectiveAngle` `PerspectiveMatch` `Picture` `Pipe` `PlaceHole`
`Plan` `Planar` `PlanarDifference` `PlanarIntersection` `PlanarMesh` `PlanarSrf`
`PlanarUnion` `Plane` `PlaneThroughPt` `PlayAnimation` `Point` `PointCloud`
`PointCloudContour` `PointCloudSection` `PointDeviation` `PointGrid` `PointLight` `Points`
`PointsFromUV` `PointsOff` `PointsOn` `PolarZonohedron` `Polygon` `PolygonCount`
`Polyhedron` `Polyline` `PolylineOnMesh` `PopupMenu` `PopupPopular` `PopupToolbar`
`PrevDetail` `PrevU` `PrevV` `PrevViewport` `Print` `PrintDisplay`
`Project` `ProjectOsnap` `ProjectToCPlane` `Properties` `PropertiesPage` `PtOffSelected`
`Pull` `Purge` `PurgeOrphanDrawings` `PurgeRefObjects` `PushPull` `PushViewportToBack`
`Pyramid`

### Q（4）

`QuadRemesh` `QuadrangulateMesh` `QuickHull` `QuickText`

### R（88）

`RLeaderEdit` `RTextEdit` `Rack` `Radiate` `RadiateFind` `Radius`
`RailRevolve` `ReadCommandFile` `ReadEveryIGESEntity` `ReadViewportsFromFile` `Rebuild` `RebuildCrvNonUniform`
`RebuildEdges` `RebuildMesh` `RebuildMeshNormals` `RebuildOld` `RebuildUV` `RecordAnimation`
`Rectangle` `RectangularLight` `Redo` `RedoMultiple` `RedoSelection` `RedoView`
`ReduceMesh` `ReducePointCloud` `ReducePolyline` `RefitTrim` `Reflect` `RefreshAllTextures`
`RefreshShade` `ReleaseFromCage` `RemapCPlane` `RememberCopyOptions` `RemoveAllNakedMicroEdges` `RemoveControlPoint`
`RemoveCrease` `RemoveFromGroup` `RemoveGuide` `RemoveKnot` `RemoveMappingChannel` `RemoveMultiKnot`
`RemovePerFaceColors` `RemoveSymmetry` `Render` `RenderArctic` `RenderAssignMaterialToLayer` `RenderAssignMaterialToLayersOfObjects`
`RenderAssignMaterialToObjects` `RenderBlowup` `RenderInWindow` `RenderMergeIdenticalMaterials` `RenderOpenLastRendering` `RenderOpenRenderImage`
`RenderPreview` `RenderPreviewInWindow` `RenderPreviewWindow` `RenderWindow` `Rendering` `RepairSubD`
`Reparameterize` `Repeat` `ReplaceBlock` `ReplaceEdge` `ReportProblem` `Rescue3dmFile`
`RescueBlockOrphans` `Reset` `ResetMessageBoxes` `Restore` `RevCloud` `Revert`
`Revolve` `RevolvedHole` `RhinoCyclesReport` `RhombicSpirallohedron` `Rib` `Ribbon`
`RibbonOffset` `Rotate` `Rotate3D` `RotateCamera` `RotateHole` `RotateView`
`RoundHole` `Run` `RunPythonScript` `RunScript`

### S（293）

`STEPTree` `Save` `SaveACopy` `SaveAs` `SaveAsTemplate` `SaveClippingSectionCPlanes`
`SaveClippingSectionViews` `SaveCurrentTagFilter` `SaveRenderWindowAs` `SaveSmall` `SaveWindowLayout` `Scale`
`Scale1D` `Scale2D` `ScaleByPlane` `ScaleEach` `ScaleNU` `ScalePositions`
`ScaleTextHeight` `ScreenCaptureToClipboard` `ScreenCaptureToFile` `ScriptEditor` `Section` `SectionBox`
`SelAll` `SelAnnotationStyle` `SelBadObjects` `SelBaked` `SelBlockInstance` `SelBlockInstanceNamed`
`SelBoundary` `SelBox` `SelBrush` `SelBrushPoints` `SelCaptives` `SelChain`
`SelChildren` `SelCircular` `SelClippingPlane` `SelClippingPlaneInViewport` `SelClosedCrv` `SelClosedMesh`
`SelClosedPolysrf` `SelClosedSrf` `SelClosedSubD` `SelColor` `SelConnected` `SelConnectedMeshFaces`
`SelControlPoint` `SelControlPointRegion` `SelControls` `SelCrossing` `SelCrv` `SelDetail`
`SelDim` `SelDimAngular` `SelDimCentermark` `SelDimLinear` `SelDimOrdinate` `SelDimOverride`
`SelDimRadial` `SelDimTextOverride` `SelDot` `SelDup` `SelDupAll` `SelEdgeLoop`
`SelEdgeRing` `SelExtrusion` `SelFaceLoop` `SelFacesToBoundary` `SelFence` `SelFontUse`
`SelGroup` `SelHatch` `SelHatchPattern` `SelID` `SelIsolated` `SelKey`
`SelKeyValue` `SelLast` `SelLayer` `SelLayerNumber` `SelLeader` `SelLight`
`SelLine` `SelLinetype` `SelMappingWidget` `SelMaterialName` `SelMesh` `SelMeshEdges`
`SelMeshFacesByArea` `SelMeshFacesByAspectRatio` `SelMeshFacesByDraftAngle` `SelMeshFacesByEdgeLength` `SelMeshPart` `SelMirroredBlocks`
`SelNakedMeshEdgePt` `SelName` `SelNamedViewWidget` `SelNonManifold` `SelNone` `SelObjectsWithBrokenHistory`
`SelObjectsWithHistory` `SelOpenCrv` `SelOpenMesh` `SelOpenPolysrf` `SelOpenSrf` `SelOpenSubD`
`SelOrphanDrawings` `SelParents` `SelPicture` `SelPlanarCrv` `SelPlanarSrf` `SelPolyline`
`SelPolysrf` `SelPrev` `SelPt` `SelPtCloud` `SelRectangular` `SelRenderColor`
`SelSelfIntersectingCrv` `SelShortCrv` `SelSmall` `SelSrf` `SelSubD` `SelSubDCrv`
`SelSubDEdges` `SelText` `SelTrimmedSrf` `SelU` `SelUV` `SelUntrimmedSrf`
`SelV` `SelValue` `SelVisible` `SelVolumeObject` `SelVolumePipe` `SelVolumeSphere`
`SelWindow` `Select` `SelectFacesByNormal` `SelectionFilter` `SelectionFilterEdges` `SelectionFilterEnable`
`SelectionFilterFaces` `SelectionFilterNone` `SelectionFilterToggle` `SelectionFilterVertices` `SendBackward` `SendToBack`
`SetActiveViewport` `SetCurrentAnnotationStyle` `SetCurrentRenderPlugIn` `SetCustomLinetype` `SetDetailBorder` `SetDetailScale`
`SetDimensionLayer` `SetDisplayMode` `SetDocumentUserText` `SetDotNetRuntime` `SetFlythroughAnimation` `SetGroupName`
`SetHatchBaseAndRotation` `SetIgesLayerLevelMap` `SetLayerLinetype` `SetLayerToObject` `SetLinetype` `SetLinetypeScale`
`SetMaximizedViewport` `SetMeshSurfaceParameters` `SetObjectDisplayMode` `SetObjectName` `SetOneDaySunAnimation` `SetOrtho`
`SetPathAnimation` `SetPerFaceColorByFacePack` `SetPlanar` `SetPt` `SetRedrawOff` `SetRedrawOn`
`SetSeasonalSunAnimation` `SetSnap` `SetSpotlightToView` `SetSurfaceTangent` `SetTurntableAnimation` `SetUserText`
`SetView` `SetViewToSpotlight` `SetWorkingFolder` `SetWorldOrigin` `SetZoomExtentsBorder` `Shade`
`ShadeSelected` `Shear` `Shell` `ShortPath` `Show` `ShowDir`
`ShowDirOff` `ShowEdges` `ShowEdgesOff` `ShowEnds` `ShowEndsOff` `ShowInDetail`
`ShowInViewports` `ShowLayersInDetail` `ShowOsnap` `ShowPt` `ShowRenderMesh` `ShowSelected`
`ShowSelectedInDetail` `ShowSelectedInViewport` `ShowToolBar` `ShowZBuffer` `ShrinkTrimmedSrf` `ShrinkTrimmedSrfToEdge`
`ShrinkWrap` `Silhouette` `SimplifyCrv` `Sketch` `Slab` `Slide`
`SmartTrack` `Smash` `Smooth` `Snap` `SnapSize` `SnapToLocked`
`SnapToMeshObject` `SnapToMeshes` `SnapToOccluded` `SnapToSubDObject` `Snapshots` `SoftEditCrv`
`SoftEditSrf` `SoftMove` `SoftTransform` `SolidPtOn` `SpaceMouse` `Sphere`
`SphereTangentToThreeSurfaces` `SpinSubDEdge` `Spiral` `Split` `SplitDisjointMesh` `SplitEdge`
`SplitFace` `SplitMeshEdge` `SplitMeshWithCurve` `SplitPointCloud` `SplitRefitSurface` `SplitViewportHorizontal`
`SplitViewportVertical` `Splop` `Spotlight` `Squish` `SquishBack` `SquishInfo`
`SrfControlPtGrid` `SrfPt` `SrfPtGrid` `SrfSeam` `StartScriptServer` `StepUnitsAndTolerance`
`Stitch` `Stretch` `StretchCrv` `SubCrv` `SubDBox` `SubDCone`
`SubDCylinder` `SubDEllipsoid` `SubDFromMesh` `SubDPlane` `SubDSphere` `SubDTorus`
`SubDTruncatedCone` `Subdivide` `Sun` `SunLight` `Super_Sweep` `SwapMeshEdge`
`SwapView` `Sweep1` `Sweep1SubD` `Sweep2` `Sweep2SubD` `SymbolContent`
`Symmetry` `SynchronizeCPlanes` `SynchronizeRenderColors` `SynchronizeViews` `SystemInfo`

### T（42）

`Tag` `TagFilter` `TagManager` `TagsFromLayers` `Taper` `Text`
`TextObject` `TextProperties` `Textures` `ThicknessAnalysis` `ThicknessAnalysisOff` `TiltView`
`ToExtrusion` `ToNURBS` `ToNurbsCrv` `ToSubD` `ToSubDCrv` `ToggleFloatingViewport`
`ToggleGpuProcedurals` `ToggleInstantAliases` `ToggleLeftSidebar` `ToggleLockedActiveRealtimeViewport` `TogglePausedActiveRealtimeViewport` `ToggleRenderMesh`
`ToggleRightSidebar` `ToggleSubDDisplay` `ToggleSubDFaceEdgeVertex` `Toolbar` `ToolbarLock` `Torus`
`TriangulateMesh` `TriangulateNonPlanarQuads` `TriangulateRenderMeshes` `Trim` `TruncatedCone` `TruncatedPyramid`
`Tube` `Turntable` `Tutorials` `TweenCurves` `TweenSurfaces` `Twist`

### U（29）

`UVEditor` `Undo` `UndoMultiple` `UndoSelected` `UndoSelection` `UndoView`
`Ungroup` `UngroupAll` `UnifyMeshNormals` `Unisolate` `UnisolateInViewports` `UnisolateLock`
`UnjoinEdge` `Unlock` `UnlockSelected` `UnpackTextures` `UnrollSrf` `UnrollSrfUV`
`Untrim` `UntrimAll` `UntrimBorder` `UntrimHoles` `Unweld` `UnweldEdge`
`UnweldVertex` `Unwrap` `UpdateClippingDrawings` `UseExtrusions` `UserInterfaceObjectProxy`

### V（18）

`VariableBlendSrf` `VariableChamferSrf` `VariableFilletSrf` `VariableOffsetSrf` `Vectorize` `ViewCaptureToClipboard`
`ViewCaptureToFile` `ViewClippingSections` `ViewFirstFrame` `ViewFrameNumber` `ViewLastFrame` `ViewNextFrame`
`ViewPreviousFrame` `ViewportProperties` `ViewportTabs` `Volume` `VolumeCentroid` `VolumeMoments`

### W（11）

`WalkAbout` `Waterman` `WebBrowser` `Weight` `Weld` `WeldEdge`
`WeldVertices` `What` `WindowLayout` `WireCut` `Worksession`

### X（2）

`XNurbs` `XNurbsHelp`

### Z（10）

`Zebra` `ZebraOff` `Zoom` `Zoom1To1Calibrate` `ZoomClippingDrawings` `ZoomEnds`
`ZoomLens` `ZoomNaked` `ZoomNonManifold` `ZoomZeroToOne`

### 其他（4）

`3DFace` `3View` `4View` `基准面`

## 3. 与 FeatureWorks 直接相关的族（速查）

- 取消修剪：`Untrim` `UntrimAll` `UntrimBorder` `UntrimHoles` `ShrinkTrimmedSrf` `ShrinkTrimmedSrfToEdge` `RefitTrim` `SelTrimmedSrf` `SelUntrimmedSrf`
- 删面重缝：`DeleteFaces` `ExtractSrf` `DupFaceBorder` `RebuildEdges` `CreateSolid` `MergeSrf` `MergeAllCoplanarFaces` `ReplaceEdge` `SplitFace`
- 正向生成：`FilletEdge` `ChamferEdge` `VariableFilletSrf` `MakeHole` `BooleanDifference` `WireCut` `Cap` `BlendSrf` `MatchSrf`
- 选择/框选：`SelFaceLoop` `SelEdgeLoop` `SelChain` `SelConnected` `SelCrossing` `SelFence` `SelBox` `SelBrush` `SelParents` `SelChildren`
- 显示/视图：`SetDisplayMode` `SetObjectDisplayMode` `ClearAllObjectDisplayModes` `SynchronizeCPlanes` `CopyCPlaneToAll` `CopyCPlaneSettingsToAll`
- 建模历史：`History` `HistoryUpdate` `HistoryPurge` `SelObjectsWithHistory` `SelObjectsWithBrokenHistory`（**construction history，不是特征树**）
- 本插件：`FWSelect` `FWFocus` `FWCancel` `FWCancelPanel` `FWPanel` `FWRebuild` `FW2Panel`（后两者属已降级的 v2 实验线）

> 精讲、官方原文要点、命令与 RhinoCommon API 的对照见同目录 `rhino-command-reference.md`。

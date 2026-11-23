# Grasshopper 组件索引（Rhino 9 活进程导出）

> **数据源**：运行中的 Rhino 9（9.1.26314.9001）+ GH1，经 `Grasshopper.Instances.ComponentServer.ObjectProxies` 导出，
> **2336 个对象 / 29 个类别**，不是网页抄录。
>
> **这是「组件层」索引**，与 `rhino-command-index.md`（命令层，1256 条）互补：
> 命令 = 你在命令行敲的操作；组件 = 你在画布里连的电池。同一个几何能力两边都有入口，但数据流只有组件层有。
>
> 全量明细可用 `scripts/Export_GH_Components.py` 在 Rhino Python 里重跑导出（升级/装新插件后刷新）。

**纪律**：日常不要通读本文档。要查组件 → 用 `g1_search_components`（最准，含描述与参数）；
要查「这类里有哪些」→ 查本文档对应小节；要查原理 → 读 `grasshopper-spatial-logic.md`。

## 1. 类别总览

| 类别 | 条数 | 来源 |
|---|---:|---|
| `Rhino` | 205 | 原生 |
| `Params` | 183 | 原生 |
| `Maths` | 156 | 原生 |
| `Curve` | 144 | 原生 |
| `Surface` | 129 | 原生 |
| `Sets` | 126 | 原生 |
| `Kangaroo2` | 120 | 官方插件 |
| `Mesh` | 103 | 原生 |
| `Vector` | 98 | 原生 |
| `Transform` | 88 | 原生 |
| `Intersect` | 59 | 原生 |
| `Display` | 53 | 原生 |
| `Vipers` | 158 | 插件 |
| `BIM-秋` | 156 | 插件 |
| `NGon` | 122 | 插件 |
| `LunchBox` | 85 | 插件 |
| `Human` | 70 | 插件 |
| `Axolotl` | 70 | 插件 |
| `Crystallon` | 67 | 插件 |
| `Wb` | 40 | 插件 |
| `Scalar` | 25 | 插件 |
| `Complex` | 18 | 插件 |
| `Dendro` | 17 | 插件 |
| `Anemone` | 16 | 插件 |
| `IntraLattice` | 15 | 插件 |
| `Chromodoris` | 9 | 插件 |
| `User` | 2 | 插件 |
| `Intralattice` | 1 | 插件 |
| `X` | 1 | 插件 |

GH 核心合计 **1344**，官方插件 Kangaroo2 **120**，第三方插件合计 **872**（共 2336）。

## 2. 原生组件全量清单（按类别，去除 obsolete/hidden）

### `Rhino`（204）

- Addition Texture · Aligned Dimension(DimAligned) · Angle Dimension (Arc)(DimAngle-A) · Angle Dimension (Lines)(DimAngle-L)
- Angle Dimension (Points)(DimAngle-P) · Annotation Arrow Settings(AS-Arrows) · Annotation Dimension Settings · Annotation Dot(Dot)
- Annotation Leader Settings(AS-Leaders) · Annotation Style · Annotation Style Overrides(A-Style) · Annotation Text Overrides(A-Text)
- Annotation Text Settings(AS-Text) · Annotation Tolerance Settings · Annotation Units Settings(AS-Units) · Bitmap Texture
- Blend Material · Blend Texture · Box Texture Mapping · Bump Texture
- Centermark · Checker Texture(Checker) · Clipping Drawing Settings · Colour Gradient
- Contains Text Filter(Contains) · Content Cache(Cache) · Content Identity(Identity) · Content Information
- Convert Units(C-Units) · Create Clipping Drawing · Custom Material · Custom Mesh Texture Mapping
- Cylinder Texture Mapping · Directional Light(D-Light) · Display Attributes(Display) · Display Colour
- Dots Texture · Double Sided Material · Drafting Attributes(Drafting) · Drafting Scale
- Duplicate Content · Effective Annotation Settings · Effective Object Attributes · Emission Material
- Equality Filter(Equals) · Evaluate Annotation Text(Evaluate) · Evaluate Text Fields(Evaluate) · Explode Clipping Drawing
- Explode Object(Explode) · Export Hatch Pattern(E-Hatch) · Export Material(E-Material) · Export Model Block Definition(E-Block)
- Export Options(EOptions) · Export Options 3DM(EO-3DM) · Export Options ACIS(EO-ACIS) · Export Options AutoCAD(EO-ACAD)
- Export Options FBX(EO-FBX) · Export Options IGES(EO-IGES) · Export Options SKP(EO-SKP) · Export Options STEP(EO-STEP)
- Export Options STL(EO-STL) · Export Texture · Exposure Texture · Extract Sections
- Extract Slices · fBm Texture · Filter Content(Filter) · Gem Material
- Glass Material · Gradient Colour Stop · Gradient Texture · Granite Texture
- Greater Than Filter(Greater) · Grid Texture · Group Content(Group) · Hide Model Layer(L-Hide)
- High Dynamic Range Texture · Import Content(Import) · Import Hatch Pattern(I-Hatch) · Import Material(I-Material)
- Import Model Block Definition(I-Block) · Import Model Environment · Import Texture(I-Texture) · Intersection Filter
- Invert Texture · Is Filter(Is) · Item Display Colour · Layout Viewport
- Leader · Less Than Filter(Less) · Light Attributes(Light) · Linear Dimension(DimLinear)
- Linear Light · Lines Pattern(L-Pattern) · Logical And Filter(And) · Logical Not Filter(Not)
- Logical Or Filter(Or) · Marble Texture · Mask Texture · Match Text Filter(Match)
- Material Shader(Shader) · Mesh Texture Coordinates · Metal Material · Model Basic Environment
- Model Block Definition · Model Block Instance · Model Clipping Plane · Model CPlane(CPlane)
- Model Earth Location · Model Font(Font) · Model Hatch(Hatch) · Model Hatch Line(Hatch Line)
- Model Hatch Pattern · Model Layer(Layer) · Model Linetype(Linetype) · Model Object(Object)
- Model Section Style · Model View(View) · Model Viewport · Multiplication Texture
- Noise Texture · Object Display Colour · Object Display Mode · Object Linetype
- Object Linetype(Linetype) · Object Material · Object Material · Object Print Colour
- Object Print Width · Object Section Style · Object Type(OT) · Objects Clipped
- OCS Texture Mapping · Order Content(Order) · Ordinate Dimension · Page Settings
- Paint Material · Perlin Marble Texture · Perturbing Texture · Physical Sky Texture
- Physically Based Material · Picture Material · Planar UV Texture Mapping · Planar UVW Texture Mapping
- Plaster Material · Plastic Material · Point Light · Print Colour
- Print Width · Query Annotation Styles(Styles) · Query Directory(Directory) · Query Installed Fonts(Fonts)
- Query Layout Objects(L-Objects) · Query Layouts(Layouts) · Query Model Block Definitions · Query Model Environments
- Query Model Hatch Patterns(Hatches) · Query Model Layers(Layers) · Query Model Lights(Lights) · Query Model Linetypes(Linetypes)
- Query Model Location · Query Model Materials(Materials) · Query Model Objects(M-Objects) · Query Model Section Styles
- Query Model Textures(Textures) · Query Named CPlanes(CPlanes) · Query Named Views · Query Objects(Objects)
- Query Viewports(Viewports) · Radial Dimension(DimRadial) · Rectangular Light · Render Attributes(Render)
- Render Lighting Options(Render) · Resample Texture · Save Texture Image(Save Image) · Section Attributes(Section)
- Select Geometry(Select) · Serial Dimension · Simple Bitmap Texture · Single Color Texture
- Skylight · Sphere Texture Mapping · Spotlight · Stucco Texture
- Sun · Sun (Manual Control)(Sun) · Sun Preview(S-Preview) · Surface Texture Mapping
- Text Entity(Text) · Text Field Expression · Texture Color Adjustment · Texture Evaluator(Evaluator)
- Texture Mapping Adjustment · Texture Mapping Properties · Texture Slot · Tile Texture
- Turbulence Texture · Union Filter(Union) · Unit System(U-System) · User Text(U-Text)
- Visibility Attributes(Visibility) · Waves Texture · Wood Texture · Zoom Extents(Zoom Ext)

### `Params`（179）

- < · Angular Dimension · Annotation Dot · Arrow
- Arrow Settings(Arrows) · Atom · Atom Data(Atom) · Bifocals
- Block Instance · Boolean(Bool) · Boolean Signal · Boolean Toggle(Toggle)
- Box · Brep · Button · Cache
- Cache Access · Calendar · Centermark · Cherry Picker(Item)
- Circle · Circular Arc(Arc) · Clipping Arrow(Arrow) · Clipping Drawing Settings
- Clipping Plane · Clock · Cluster · Cluster Input(Input)
- Cluster Output(Output) · Color Gradient(Gradient) · Color Stop · Colour(Col)
- Colour Picker(Colour) · Colour Swatch(Swatch) · Colour Wheel(Wheel) · Complex(C)
- Constant(constant) · Construction Plane(CPlane) · Content Viewer(Viewer) · Context Bake(C-Bake)
- Context Print(C-Print) · Control Knob(Knob) · Culture · Curve(Crv)
- Data · Data Dam(Dam) · Data Input(Input) · Data Output(Output)
- Data Path(Path) · Data Recorder(Rec) · Data Signal(Signal) · Date Time Format(Format)
- Digit Scroller · Dimension Settings(Dimension) · Display Mode · Domain
- Domain² · Earth Anchor Point(Anchor) · Expression(Exp) · Extrusion
- Field · File Path(Path) · Fitness Landscape(LScape) · Font
- Galapagos · Gene Pool(Genes) · Geometry(Geo) · Geometry Cache
- Geometry Pipeline(Pipeline) · Get Boolean · Get Data · Get File Path
- Get Geometry · Get Integer · Get Line · Get Number
- Get Object · Get Plane · Get Point · Get String
- Gradient · Graph Mapper(Graph) · Group(Grp) · Group
- Guid(ID) · Hatch · Hatch Line · Image Resource
- Image Sampler(Image) · Import 3DM(3DM) · Import Coordinates(Coords) · Import Image(IMG)
- Import PDB(PDB) · Import SHP(SHP) · Integer(Int) · Jump
- Layout Viewport(Layout) · Leader · Leader Settings(Leaders) · Light
- Line · Linear Dimension · Location(Loc) · Marshalling signal parameter(Data)
- Match Text · Matrix · MD Slider · Mesh
- Mesh Face(Face) · Mesh Point(MPoint) · Mesher Settings(Mesh) · Model Action(Action)
- Model Annotation Style(Style) · Model Attribute Key(Key) · Model Block Definition · Model Content(Content)
- Model Environment · Model Hatch Pattern · Model Layer(Layer) · Model Linetype(Linetype)
- Model Material(Material) · Model Mesher Settings · Model Object(Object) · Model Print Width
- Model Section Style · Model Sun(Sun) · Model Texture(Texture) · Model Texture Mapping(Mapping)
- Model Viewport(Viewport) · Number(Num) · Number Set(NumSet) · Number Slider
- Object Details(ObjDet) · Object Display(Display) · Object Drafting(Drafting) · Object Render(Render)
- Object Visibility(Visibility) · Oh noes!(LolCat) · Ordinate Dimension · Page Settings
- Panel · Param Viewer(Viewer) · Plane(Pln) · Point(Pt)
- Point Cloud(PCloud) · Predicate · Radial Dimension · Read File(File)
- Receiver · Rectangle(Rec) · Relay · Scribble
- SectionBox(SBox) · Shader · Size Vector(SVec) · Sketch
- Standard Viewport(Viewport) · SubD · Suirify · Surface(Srf)
- Symbol Display(SymDis) · Text(Txt) · Text Balloon(Balloon) · Text Entity
- Text Settings(Texts) · Texture Slot · Time · Timeline
- Tolerance Settings(Tolerances) · Transform · Trigger · Twisted Box(TBox)
- Unit System · Units Settings(Units) · Value List(List) · Value Picker
- Variant(Var) · Vector(Vec) · View

### `Maths`（125）

- Absolute(Abs) · Addition(A+B) · ArcCosine(ACos) · ArcSine(ASin)
- ArcTangent(ATan) · Assert True(AT) · Average(Avr) · Blur Numbers(NBlur)
- Bounds(Bnd) · Bounds 2D(Bnd) · C# Script(C#) · Centroid
- Circumcentre(CCentre) · Clamp · Combine Date & Time(CDate) · Complex Argument(Arg)
- Complex Components(Complex) · Complex Conjugate(z*) · Complex Modulus(CMod) · Consecutive Domains(Consec)
- Construct Date(Date) · Construct Domain(Dom) · Construct Domain²(Dom²) · Construct Domain²(Dom²Num)
- Construct Exotic Date(DateEx) · Construct Matrix(Matrix) · Construct Smooth Time(SmTime) · Construct Time(Time)
- CoSecant(Csc) · Cosine(Cos) · CoTangent(Cot) · Create Complex(Complex)
- Cube · Cube Root(Cbrt) · Date Range(RDate) · Deconstruct Date(DDate)
- Deconstruct Domain(DeDomain) · Deconstruct Domain²(DeDom2Num) · Deconstruct Domain²(DeDom2) · Deconstruct Matrix(DeMatrix)
- Degrees(Deg) · Display Matrix(Matrix) · Dispose Document(DD) · Divide Domain(Div)
- Divide Domain²(Divide) · Division(A/B) · DotNET C# Script (LEGACY)(C#) · DotNET VB Script (LEGACY)(VB)
- Epsilon(Eps) · Equality(Equals) · Evaluate(Eval) · Expression
- Extremes(Extrz) · Factorial(Fac) · Find Domain(FDom) · Gate And(And)
- Gate Majority(Vote) · Gate Nand(Nand) · Gate Nor(Nor) · Gate Not(Not)
- Gate Or(Or) · Gate Xnor(Xnor) · Gate Xor(Xor) · Golden Ratio(Phi)
- Incentre(ICentre) · Includes(Inc) · Integer Division(A\B) · Interpolate data(Interp)
- Interpolate Date(IntDate) · Invert Matrix(MInvert) · IronPython 2 Script(IPy2) · Larger Than(Larger)
- Log N(LogN) · Logarithm(Log) · Mass Addition(MA) · Mass Multiplication(MM)
- Maximum(Max) · Minimum(Min) · Modulus(Mod) · Multiplication(A×B)
- Natural logarithm(Ln) · Natural logarithm(E) · Negative(Neg) · One Over X(1/x)
- Orthocentre(OCentre) · PerlinNoise(Perlin) · Pi · Power(Pow)
- Power of 10(10º) · Power of 2(2º) · Power of E(Eº) · Python 3 Script(Py3)
- Radians(Rad) · Relative Differences(RelDif) · Remap Numbers(ReMap) · Right Trigonometry(RTrig)
- Round · Script(S) · Script Input/Output Parameter(SP) · Script Library(L)
- Script Library (Deconstruct)(DSL) · Script Parameter (Deconstruct)(DSP) · Script Source(S) · Script Source (Deconstruct)(DS)
- Secant(Sec) · Series Addition(SA) · Similarity(Similar) · SimplexNoise(Simplex)
- Sinc · Sine(Sin) · Smaller Than(Smaller) · Smooth Numbers(Smooth)
- Square(Sqr) · Square Root(Sqrt) · Subtraction(A-B) · Swap Columns(SwapC)
- Swap Rows(SwapR) · Tangent(Tan) · Transpose Matrix(Transpose) · Triangle Trigonometry(Trig)
- Truncate(Trunc) · var · Variable(var) · VB Script(VB)
- Weighted Average(Wav)

### `Curve`（120）

- Arc · Arc 3Pt(Arc) · Arc SED(Arc) · Bezier Span(BzSpan)
- BiArc · Blend Curve(BlendC) · Blend Curve Pt(BlendCPt) · Catenary(Cat)
- Catenary Ex(CatEx) · Circle(Cir) · Circle 3Pt(Circle) · Circle CNR(Circle)
- Circle Fit(FCircle) · Circle Fit(FCircle) · Circle TanTan(CircleTT) · Circle TanTanTan(CircleTTT)
- Closed(Cls) · Connect Curves(Connect) · Contour (ex)(Contour) · Control Points(CP)
- Control Polygon(CPoly) · Curvature · Curvature Graph(CrvGraph) · Curve Blend(CBlend)
- Curve Closest Point(Crv CP) · Curve Contour(Contour) · Curve Depth(Depth) · Curve Domain(CrvDom)
- Curve Frame(Frame) · Curve Frames(Frames) · Curve Middle(MidPt) · Curve Nearest Object(CrvNear)
- Curve On Surface(CrvSrf) · Curve Proximity(CrvProx) · Curve Side(Side) · Curve To Polyline(ToPoly)
- Dash Pattern(Dash) · Deconstruct Arc(DArc) · Deconstruct Rectangle(DRec) · Derivatives(CDiv)
- Discontinuity(Disc) · Divide By Deviation(DivideDev) · Divide Curve(Divide) · Divide Distance(DivDist)
- Divide Length(DivLength) · Ellipse · End Points(End) · Evaluate Curve(Eval)
- Evaluate Length(Eval) · Explode · Extend Curve(Ext) · Extremes(X-tremez)
- Fillet · Fillet · Fillet Distance(Fillet) · Fit Curve(Fit)
- Fit Line(FLine) · Flip Curve(Flip) · Geodesic · Horizontal Frame(HFrame)
- Horizontal Frames(HFrames) · InCircle · InEllipse · Interpolate(IntCrv)
- Interpolate (t)(IntCrv(t)) · Iso Curve(Iso) · Join Curves(Join) · Kinky Curve(KinkCrv)
- Knot Vector(Knots) · Length(Len) · Length Domain(LenD) · Length Parameter(LenP)
- Line(Ln) · Line 2Plane(Ln2Pl) · Line 4Pt(Ln4Pt) · Line SDL(Line)
- Match Curve(MatchCrv) · Modified Arc(ModArc) · Nurbs Curve(Nurbs) · Nurbs Curve PWK(NurbCrv)
- Offset Curve(Offset) · Offset Curve Loose(Offset (L)) · Offset Loose 3D · Offset on Srf(OffsetS)
- Offset Polyline(OP) · Perp Frame(PFrame) · Perp Frames(PFrames) · Planar
- Point In Curve(InCurve) · Point in Curves(InCurves) · Point On Curve(CurvePoint) · PolyArc(PArc)
- Polygon · Polygon Center(PCen) · Polygon Edge(PolEdge) · PolyLine(PLine)
- Polyline Collapse(PCol) · Project Curve(Project) · Pull Curve(Pull) · Rebuild Curve(ReB)
- Rectangle · Rectangle 2Pt(Rec 2Pt) · Rectangle 3Pt(Rec 3Pt) · Reduce(RedPLine)
- Seam · Segment Lengths(LenSeg) · Shatter · Simplify Curve(Simplify)
- Smooth Polyline · Sub Curve(SubCrv) · Swing Arc(Swing) · Tangent Arcs(TArc)
- Tangent Curve(TanCurve) · Tangent Lines(Tan) · Tangent Lines (Ex)(TanEx) · Tangent Lines (In)(TanIn)
- Torsion · Tween Curve(TweenCrv) · TwoByFourJam(2x4 Jam) · Vectorize

### `Surface`（107）

- 4Point Surface(Srf4Pt) · Area · Area Moments(AMoments) · Boundary Surfaces(Boundary)
- Bounding Box(BBox) · Box 2Pt(Box) · Box Corners · Box Properties(BoxProp)
- Box Rectangle(BoxRec) · Brep Closest Point(Brep CP) · Brep Edges(Edges) · Brep Join(Join)
- Brep Topology(Topology) · Brep Wireframe(Wires) · Cap Holes(Cap) · Cap Holes Ex(CapEx)
- Center Box(Box) · Closed Edges(EdgesCls) · Cone · Continuous Patch(CPatch)
- Control Point Loft(CPLoft) · Convex Edges(EdgesCvx) · Copy Trim(Trim) · Cylinder(Cyl)
- Deconstruct Box(DeBox) · Deconstruct Brep(DeBrep) · Dimensions(Dim) · Divide Surface(SDivide)
- Domain Box(Box) · Edge Surface(EdgeSrf) · Edges from Directions(EdgesDir) · Edges from Faces(EdgesFaces)
- Edges from Length(EdgesLen) · Edges from Linearity(EdgesLin) · Edges from Points(EdgesPt) · Evaluate Box(Box)
- Evaluate SubD(EvalSubD) · Evaluate Surface(EvalSrf) · Extrude(Extr) · Extrude Along(ExtrCrv)
- Extrude Angled(ExtrAng) · Extrude Linear(Extrude) · Extrude Point(Extr) · Fillet Edge(FilEdge)
- Fit Loft(FitLoft) · Flip · Fragment Patch(FPatch) · Is Planar(Planar)
- Isotrim(SubSrf) · Loft · Loft Options(Loft Opt) · Loft Options(Loft)
- Merge Faces(FMerge) · Mesh from SubD(MeshSubD) · MultiPipe(MP) · MultiPipe(MP)
- Network Surface(NetSurf) · Offset Surface(Offset) · Offset Surface Loose(Offset (L)) · Osculating Circles(Osc)
- Patch · Pipe · Pipe Variable(VPipe) · Plane Surface(PlaneSrf)
- Plane Through Shape(PxS) · Point In Brep(BrepInc) · Point In Breps(BrepsInc) · Point In Trim(TrimInc)
- Principal Curvature(Curvature) · Quad Sphere(QSph) · Rail Revolution(RailRev) · Retrim
- Reverse Surface · Revolution(RevSrf) · Ruled Surface(RuleSrf) · Set SubD Edge Sharpness
- Shape In Brep(ShapeIn) · Sphere(Sph) · Sphere 4Pt(Sph4Pt) · Sphere Fit(SFit)
- SubD Box(SubDBox) · SubD Closest Point(SubD CP) · SubD Control Polygon(SubDPoly) · SubD Edge Sharpness(SubDSharp)
- SubD Edge Tags(SubDTags) · SubD Edges(SubDEdges) · SubD Faces(SubDFaces) · SubD from Mesh(SubDMesh)
- SubD Fuse(Fuse) · SubD To Brep(ToBrep) · SubD Vertex Tags(SubDVTags) · SubD Vertices(SubDVerts)
- Sum Surface(SumSrf) · Surface Boundaries(SrfBnd) · Surface Closest Point(Srf CP) · Surface Curvature(Curvature)
- Surface Frames(SFrames) · Surface From Points(SrfGrid) · Surface Inflection(SInf) · Surface Points(SrfPt)
- Sweep1(Swp1) · Sweep2(Swp2) · Transpose Surface(Transpose) · Untrim
- Variable Fillet Edge(VFilEdge) · Volume · Volume Moments(VMoments)

### `Sets`（99）

- Carthesian Product(CProd) · Char Sequence(CharSeq) · Characters(Chars) · Clean Tree(Clean)
- Clean Tree(Clean) · Combine Data(Combine) · Concatenate(Concat) · Construct Path(Path)
- Create Set(CSet) · Cross Reference(CrossRef) · Cull Index(Cull i) · Cull Nth(CullN)
- Cull Pattern(Cull) · Deconstruct Path(DPath) · Delete Consecutive(DCon) · Disjoint
- Dispatch · Duplicate Data(Dup) · Entwine · Explode Tree(BANG!)
- Fibonacci(Fib) · Find similar member(FSim) · Flatten Tree(Flatten) · Flip Matrix(Flip)
- Format · Graft Tree(Graft) · Insert Items(Ins) · Item Index(Index)
- Jitter · Key/Value Search(KeySearch) · List Item(Item) · List Length(Lng)
- Longest List(Long) · Match Text(TMatch) · Match Tree(Match) · Member Index(MIndex)
- Merge · Merge · Merge 03(M3) · Merge 04(M4)
- Merge 05(M5) · Merge 06(M6) · Merge 08(M8) · Merge 10(M10)
- Merge Multiple(Merge) · Null Item(Null) · Partition List(Partition) · Path Compare(Compare)
- Path Mapper · Pick'n'Choose(P'n'C) · Prune Tree(Prune) · Random
- Random Reduce(Reduce) · RandomEx(RndEx) · Range · Relative Item(RelItem)
- Relative Items(RelItem2) · Repeat Data(Repeat) · Replace Items(Replace) · Replace Members(Replace)
- Replace Nulls(NullRep) · Replace Paths(Replace) · Replace Text(Rep) · Reverse List(Rev)
- Sequence(Seq) · Series · Set Difference(Difference) · Set Difference (S)(ExDiff)
- Set Intersection · Set Majority(Majority) · Set Union(SUnion) · Shift List(Shift)
- Shift Paths(PShift) · Shortest List(Short) · Sift Pattern(Sift) · Simplify Tree(Simplify)
- Sort List(Sort) · Sort Text(TSort) · Split List(Split) · Split Tree(Split)
- Stack Data(Stack) · Stream Filter(Filter) · Stream Gate(Gate) · Sub List(SubSet)
- SubSet · Text Case(Case) · Text Distance(TDist) · Text Fragment(Fragment)
- Text Join(Join) · Text Length(Len) · Text On Surface(TextSrf) · Text Split(Split)
- Text Trim(Trim) · Tree Branch(Branch) · Tree Item(Item) · Tree Statistics(TStat)
- Trim Tree(Trim) · Unflatten Tree(Unflatten) · Weave

### `Kangaroo2`（120）

- AlignFaces · Anchor · Anchor · AnchorXYZ
- Angle · AngleSnap(AS) · Beam · Bipartite
- Bomb(B) · BouncySolver · ByParent · Checkerboard
- ClampAngle · ClampLength · CoCircular · Coincident(C)
- CoLinear · Collide2d(C2d) · Collider · Combine&Clean(Clean)
- Concentric · Conicalize(Conical) · ConstantTension(CT) · CoPlanar
- CoSpherical · CurveCollide(CC) · CurvePointCollide(CPC) · CyclicQuad
- CyclicQuad · Developablize · Diagonalize(Diag) · Direction
- DotDisplay(Dot) · DynamicWeight1d(DW) · EdgeLengths · EqualAngle(EA)
- EqualLength · FaceFaceOffset(FaceFace) · Floor · FloorFriction(Floor)
- FoldAngle · G2 · Grab · Grab
- Grab · Grab · Hinge · HingePoints
- ImageCircles(ImgCircles) · interconnectPoints(inter) · Isothermic(Iso) · Length(Line)
- Length(Pts) · LengthRatio · LengthSnap · LiveSoap(LS)
- Load · Load · MagnetSnap(MS) · MeshCorners(MC)
- MeshDirection(MD) · MeshMap · MeshTurn(Turn) · Möbius Transformation(MB)
- NakedVertices(NV) · NoFoldThrough · OnCurve · OnMesh
- OnPlane · PlanarityAnalysis(PA) · Planarize · PlasticAnchor
- PlasticAnchor · PlasticHinge(PH) · PlasticLength(PL) · PolygonArea
- Pressure · Refine · RefineStrips(Strips) · RemeshByColour
- remesher · removeDuplicateLines(dupLn) · removeDuplicatePts(dupPt) · RigidBody
- RigidBody · RigidBody · RigidBodyCollide · RigidPointSet
- Rod · Show · Simple · SimpleRemesh
- Smooth · SoapFilm(SG) · SoapFilm(SG) · Soft & Hard Solver
- SoftBodyCollide · SolidPlaneCollide · SolidPointCollide(SPC) · Solver
- Solver · Solver · SphereCollide(SC) · SplitAtCorners
- StepSolver · Stripper · Support · Support
- TangentCircles(TC) · TangentialSmooth(TSmooth) · TangentIncircles · TangentIncircles
- Transform · Unroller · VertexLoads · VertexNeighbours(VN)
- Volume · WarpWeft · Wind · ZombieSolver

### `Mesh`（97）

- Align Vertices(AlignVert) · Blur Mesh(MBlur) · Construct Mesh(ConMesh) · Convex Hull(Hull2D)
- Convex Hull 3D(Hull3D) · Conway · Cull Faces(CullF) · Cull Vertices(CullV)
- Deconstruct Face(DeFace) · Deconstruct Mesh(DeMesh) · Delaunay Edges(Con) · Delaunay Mesh(Del)
- Delete Faces(DeleteF) · Delete Vertices(DeleteV) · Diffuse Sphere · Disjoint Mesh(Disjoint)
- Exposure · Face Boundaries(FaceB) · Face Circles(FaceC) · Face Normals(FaceN)
- Facet Dome(Facet) · Fibonacci Sphere · Flip Mesh(FlipM) · Geodesic Dome(Dome)
- IcoSphere · Mesh AddAttributes · Mesh Area(Area) · Mesh Box(MBox)
- Mesh Brep(Mesh) · Mesh Closest Point(MeshCP) · Mesh Colours(MCol) · Mesh ConvertQuads(ConvQuads)
- Mesh CullUnused Vertices · Mesh Curvature · Mesh Curvature Not Precise But Fast · Mesh Depth(MDepth)
- Mesh Edges(MEdges) · Mesh Eval(MEval) · Mesh Explode(Explode) · Mesh ExtractAttributes
- Mesh Flip(Flip) · Mesh FromPoints(FromPoints) · Mesh Inclusion(MInc) · Mesh Join(MJoin)
- Mesh NakedEdge(NakedEdge) · Mesh Plane(MPlane) · Mesh Quad(Quad) · Mesh Shadow(MShadow)
- Mesh Sphere(MSphere) · Mesh Sphere Ex(MSphereEx) · Mesh Split Plane(MSplit) · Mesh Spray(MSpray)
- Mesh Surface(Mesh UV) · Mesh Triangle(Triangle) · Mesh Triangulate · Mesh UnifyNormals
- Mesh Volume(Volume) · Mesh WeldVertices · MeshDual · Mesher Settings
- MetaBall · MetaBall(t) · MetaBall(t) Custom · Occlusion(Occ)
- OcTree(OcT) · Polar Zonohedron(Zonohedron) · Polyhedra Categories · Polyhedra Names
- Polyhedron · Proximity 2D(Prox) · Proximity 3D(Prox) · Quad Remesh(QRMesh)
- Quad Remesh Settings(QRSettings) · Quad Sphere(QuadSphere) · Quadmesh Settings(QMS) · Quadrangulate(Quad)
- QuadTree(QT) · QuickHull · Rhombic Spirallohedron · Settings (Quality)(Smooth)
- Settings (Speed)(Jagged) · ShrinkWrap(Wrap) · Simple Mesh(SMesh) · Smooth Mesh(MSmooth)
- Substrate · Triangle Sphere(TriSphere) · Triangulate(Tri) · TriRemesh
- Unify Mesh(UniM) · Unweld Mesh(Unweld) · Voronoi · Voronoi 3D(Voronoi³)
- Voronoi Cell(VCell) · Voronoi Groups(VorGroup) · Waterman · Weld Mesh(Weld)
- Zonohedron Dome(Zome)

### `Vector`（80）

- Addition(VAdd) · Adjust Plane(PAdjust) · Align Plane(Align) · Align Planes(Align)
- Amplitude(Amp) · Angle · Barycentric(BCentric) · Blend Colours(BlendCol)
- Break Field(BreakF) · Closest Point(CP) · Closest Points(CPs) · Construct Plane(Pl)
- Construct Point(Pt) · Coordinate Mask(CMask) · Cross Product(XProd) · Cull Duplicates(CullPt)
- Deconstruct(pDecon) · Deconstruct Plane(DePlane) · Deconstruct Vector(DeVec) · Direction Display(FDir)
- Distance(Dist) · Divide(VDiv) · Dot Product(DProd) · Evaluate Field(EvF)
- Field Line(FLine) · Flip Plane(PFlip) · Hexagonal(HexGrid) · Line + Line(LnLn)
- Line + Pt(LnPt) · Line Charge(LCharge) · Merge Fields(MergeF) · Multiply(VMul)
- Numbers to Points(Num2Pt) · Perpendicular Display(FPerp) · Plane 3Pt(Pl 3Pt) · Plane Closest Point(CP)
- Plane Coordinates(PlCoord) · Plane Fit(PlFit) · Plane Normal(Pl) · Plane Offset(Pl Offset)
- Plane Origin(Pl Origin) · Point Charge(PCharge) · Point Cloud Attributes · Point Cloud Closest Point
- Point Cylindrical(Pt) · Point Groups(PGroups) · Point Oriented(Pt) · Point Polar(Pt)
- Points to Numbers(Pt2Num) · Populate 2D(Pop2D) · Populate 3D(Pop3D) · Populate Geometry(PopGeo)
- Project Point(Project) · Pull Point(Pull) · Radial(RadGrid) · Rectangular(RecGrid)
- Reduce Point Cloud(Reduce) · Reverse(Rev) · Rotate(VRot) · Rotate Plane(PRot)
- Scalar Display(FScalar) · Solar Incidence(Solar) · Sort Along Curve(AlongCrv) · Sort Points(Sort Pt)
- Spin Force(FSpin) · Square(SqGrid) · Tensor Display(FTensor) · To Polar(Polar)
- Triangular(TriGrid) · Unit Vector(Unit) · Unit X(X) · Unit Y(Y)
- Unit Z(Z) · Vector 2Pt(Vec2Pt) · Vector Force(FVector) · Vector Length(VLen)
- Vector XYZ(Vec) · XY Plane(XY) · XZ Plane(XZ) · YZ Plane(YZ)

### `Transform`（65）

- Angular Widget(AWidget) · Bend Deform(Bend) · Blend Box(BlendBox) · Box Array(ArrBox)
- Box Mapping(BoxMap) · Box Morph(Morph) · Camera Obscura(CO) · Compound(Comp)
- Curve Array(ArrCurve) · Curve Widget(CWidget) · Flow · Group
- Inverse Transform(Inverse) · Kaleidoscope(KScope) · Linear Array(ArrLinear) · Maelstrom
- Map to Surface(Map Srf) · MapToBorder · MapToShape · Merge Group(GMerge)
- Mesh Cage(MCM) · Mirror · Mirror Curve(Mirror) · Mirror Surface(Mirror)
- MMMcpp · MMMcs · MorphToMesh(M2M) · Move
- Move Away From(MoveAway) · Move To Plane · Named Group(Group) · Orient
- Orient Direction(Orient) · Point Deform(PDeform) · Polar Array(ArrPolar) · Project
- Project Along(ProjectA) · Rectangle Mapping(RecMap) · Rectangular Array(ArrRec) · Rotate
- Rotate 3D(Rot3D) · Rotate Axis(RotAx) · Rotate Direction(Rotate) · Sanity XForm(MWHAHAHA!!)
- Scale · Scale NU · ShapeSolver · Shear
- Shear Angle(Shear) · Spatial Deform(Deform) · Spatial Deform (custom)(Deform) · Split
- Split Group(GSplit) · Splop · Sporph · Stretch
- Surface Box(SBox) · Surface Morph(SrfMorph) · Taper · Transform
- Transform Matrix(Matrix) · Triangle Mapping(TriMap) · Twist · Twisted Box(TBox)
- Ungroup

### `Intersect`（53）

- Boundary Volume(BVol) · Box Slits(Slits) · Brep | Brep(BBX) · Brep | Curve(BCX)
- Brep | Line(BLX) · Brep | Plane(Sec) · Clash · Collision Many|Many(ColMM)
- Collision One|Many(ColOM) · Contour · Contour (ex)(Contour) · Curve | Curve(CCX)
- Curve | Line(CLX) · Curve | Plane(PCX) · Curve | Self(CX) · IsoVist(IVist)
- IsoVist Ray(IVRay) · Line | Line(LLX) · Line | Plane(PLX) · Mesh Difference(MDif)
- Mesh Intersection(MInt) · Mesh Split(MSplit) · Mesh Union(MUnion) · Mesh | Curve(MCX)
- Mesh | Curve(MCX) · Mesh | Mesh(MMX) · Mesh | Plane(Sec) · Mesh | Ray(MeshRay)
- Multiple Curves(MCX) · Plane Region(PlReg) · Plane | Plane(PPX) · Plane | Plane | Plane(3PX)
- Point Cloud Contour(PC Contour) · Point Cloud Section(PC Section) · Region Difference(RDiff) · Region Intersection(RInt)
- Region Slits(RSlits) · Region Union(RUnion) · Solid Difference(SDiff) · Solid Intersection(SInt)
- Solid Union(SUnion) · Split Brep(Split) · Split Brep Multiple(SplitMul) · Split with Brep(Split)
- Split with Breps(Split) · Surface Split(SrfSplit) · Surface | Curve(SCX) · Surface | Line(SLX)
- Trim Solid(Trim) · Trim with Brep(Trim) · Trim with Breps(Trim) · Trim with Region(Trim)
- Trim with Regions(Trim)

### `Display`（52）

- Aligned Dimension(AlignDim) · Angular Dimension(AngleDim) · Angular Dimensions (Mesh) · Arc Dimension(ArcDim)
- Bar Graph · Circular Dimension(CircleDim) · Cloud Display(Cloud) · Colour CMYK(CMYK)
- Colour HSL(HSL) · Colour HSV(HSV) · Colour L*ab(L*AB) · Colour LCH(LCH)
- Colour RGB(RGB) · Colour RGB (f)(fRGB) · Colour XYZ(XYZ) · Create Material(Material)
- Custom Curve Preview · Custom Preview(Preview) · Custom Preview (WIP)(Preview) · Deconstruct Material(DMaterial)
- Dot Display(Dots) · Fancy Curves · Gradient Hatch(GHatch) · Image Gallery(Gallery)
- Legend · Line Dimension(LineDim) · Linear Dimension(LinearDim) · Make2D
- Make2D Parallel View · Make2D Perspective View · Make2D Rhino View(M2D Rhino) · Marker Dimension(MarkDim)
- Pattern Hatch(PHatch) · Pie Chart(Pie) · Point List(Points) · Point List(Points)
- Point Order(Order) · Quick Graph(Graph) · Serial Dimension(SerialDim) · Split AHSL(AHSL)
- Split AHSV(AHSV) · Split ARGB(ARGB) · Symbol (Advanced)(SymAdv) · Symbol (Simple)(SymSim)
- Symbol Display(Symbol) · Test Crash · Text Tag(Tag) · Text Tag 3D(Tag)
- Value Tracker(Tracker) · Vector Display(VDis) · Vector Display Ex(VDisEx) · Viewport Display

## 3. 第三方插件（只列代表，避免噪音）

| 插件类别 | 条数 | 代表组件 |
|---|---:|---|
| `Vipers` | 158 | S=a×n+b×(n+k), SuperFlipMatrix, 三角形多面体, 三角形网格, 三边长度确定三角形, 不均匀划分曲面 |
| `BIM-秋` | 156 | ACI Colors, Align Seam, Analyze Numbers, Animate Points, Arrange Grid, Arrow Curve |
| `NGon` | 122 | AddNGons, AdjustMeshVertices, BFS, Boolean, BoundaryFirstFlatenning, BrepEdges |
| `LunchBox` | 85 | 2D Truss, 3D Supershape, Arc Divide, Attractor, Attractor Wave, Braced Grid 1-D Structure |
| `Human` | 59 | Bake Geometry, Box2BoxXform, BoxMapping, Clickable Mesh, Convert To Document Units, Create/Modify Layers |
| `Axolotl` | 70 | Abs, Add, Array, Array Limited, Blend, Blur |
| `Crystallon` | 67 | Crystallon-Boundary Voxels, Crystallon-Conformal Skin, Crystallon-Connectivity Selector, Crystallon-Connectivity Type, CrystallonV2-Bezier Curve, CrystallonV2-Cell Lattice Fill |
| `Wb` | 37 | Weaverbird's Bevel Edges, Weaverbird's Bevel Vertices, Weaverbird's Blur Mesh, Weaverbird's Catmull-Clark Subdivision, Weaverbird's Constant Quads Split Subdivision, Weaverbird's Discover Covering and Retrim |
| `Scalar` | 0 | - |
| `Complex` | 0 | - |
| `Dendro` | 17 | Create Mask, Create Settings, Curve To Volume, Mask Volume, Mesh to Volume, Offset Volume |
| `Anemone` | 10 | Browse History, Fast Loop End, Fast Loop Start, Loop End, Loop Input, Loop Output |
| `IntraLattice` | 15 | Basic Box, Basic Cylinder, Clean Network, Conform Surface-Axis, Conform Surface-Point, Conform Surface-Surface |
| `Chromodoris` | 9 | Build IsoSurface, Close Voxel Data, Curvature Approximation, Draft Angle, Mesh Loft, Mesh Pipe |
| `User` | 2 | Rem(干扰）, 细分→晶格线 |
| `Intralattice` | 1 | Adjust UV |
| `X` | 1 | Example |

> 插件组件名极不统一、GUID 随版本变，**不要靠 Guid 硬编码**，用 `g1_search_components` 按名字查。

## 4. 建模常用族速查（FeatureWorks / 参数化建模场景）

### 序列 / 列表

- 有：`Series` · `Range` · `Reverse` · `Shift List` · `Sort List` · `Cull Pattern` · `Dispatch` · `Partition List` · `Split List` · `List Item` · `List Length` · `Weave`
- 本机未见：`Repeat`

### 数据树

- 有：`Simplify` · `Path Mapper` · `Param Viewer` · `Merge` · `Entwine` · `Flip Matrix` · `Shift Paths` · `Trim Tree` · `Explode Tree` · `Match Tree` · `Tree Statistics`
- 本机未见：`Graft` · `Flatten`

### 曲面 / 实体

- 有：`Center Box` · `Box 2Pt` · `Sphere` · `Cylinder` · `Plane Surface` · `Extrude` · `Loft` · `Sweep` · `Brep Join` · `Solid Union` · `Solid Difference` · `Solid Intersection` · `Cap Holes` · `Deconstruct Brep` · `Brep Edges`
- 本机未见：`Revolve` · `Brep Faces`

### 变换 / 定位

- 有：`Move` · `Rotate` · `Scale` · `Orient` · `Mirror` · `Rectangle Mapping` · `Box Mapping` · `Construct Plane` · `XY Plane`
- 本机未见：`Array Linear` · `Array Polar`

### 选择 / 筛选

- 有：`Cull Pattern` · `Cull Index` · `Dispatch` · `Null Item` · `Clean Tree` · `Sort List` · `Member Index` · `Pick'n'Choose`
- 本机未见：`Sift`

### 向量 / 点

- 有：`Construct Point` · `Deconstruct` · `Unit X` · `Unit Z` · `Vector 2Pt` · `Evaluate Surface` · `Surface Closest Point` · `Curve Closest Point`

### 分析 / 验证

- 有：`Area` · `Volume` · `Brep Closest Point` · `Point In Brep` · `Brep Topology` · `Is Planar`
- 本机未见：`Point In Curves` · `Curve Length` · `Is Closed`

## 5. 怎么查（三条路，按成本排序）

1. **`g1_search_components(query, category?, subcategory?, limit?, includeDeprecated?)`** — 最准，返回名字/类别/描述；
   多词是 AND 关系（'XY plane' 能找到 'World XY'），精确名优先排序。
2. **本文档第 1/2/3 节** — 查「这类里有什么」，不用连 Rhino。
3. **grep 导出明细** — 需要 Guid / 全量枚举时：先跑 `scripts/Export_GH_Components.py` 生成 TSV 再 grep。

## 6. 已知坑

- **GH1 vs GH2 是两套画布和两套 API**。本文件导出自 GH1（`Grasshopper.Instances`）。
  GH2 在 `Rhino 9/Plug-ins/Grasshopper2`，工具前缀是 `g2_*`，求解读回是 `g2_solve_canvas`（带逐组件诊断），**不要跨版本混用 id**。
- **组件名存在 ≠ 能用**：obsolete/hidden 的组件默认不出现，必须显式 `includeDeprecated=true` 或用 Guid 才能放。
- **`.gha` 文件在 ≠ 组件已注册**：插件要随 Rhino 启动加载后才进 ComponentServer。本机 15 个 `.gha`，实际注册出 29 个类别。
- **组件 Guid 不适合硬编码**：插件升级会变；用名字或 `search_components` 更稳。

> 原理、数据树、构造序列设计方法见 `grasshopper-spatial-logic.md`。

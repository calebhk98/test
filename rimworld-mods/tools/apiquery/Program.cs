// Lists RimWorld 1.6 types and members from the reference assemblies, so code
// and XML can be checked against the real API instead of memory.
//
//   dotnet run --project tools/apiquery -- ThingDef          members of every type named ThingDef
//   dotnet run --project tools/apiquery -- --find Glower     type names containing "Glower"
//
// A Def's public fields are the XML tags it accepts.
using System.Reflection;

var refDir = typeof(Program).Assembly.GetCustomAttributes<AssemblyMetadataAttribute>()
    .First(a => a.Key == "RimRefDir").Value;
var dlls = Directory.GetFiles(refDir, "*.dll");
using var ctx = new MetadataLoadContext(new PathAssemblyResolver(dlls));
var types = new[] { "Assembly-CSharp.dll", "UnityEngine.CoreModule.dll" }
    .Select(f => ctx.LoadFromAssemblyPath(Path.Combine(refDir, f)))
    .SelectMany(a => { try { return a.GetTypes(); } catch (ReflectionTypeLoadException e) { return e.Types.Where(t => t != null); } })
    .ToList();

if (args.Length == 0) { Console.Error.WriteLine("usage: apiquery <TypeName> | --find <substring>"); return 1; }
if (args[0] == "--find")
{
    foreach (var t in types.Where(t => t.Name.Contains(args[1], StringComparison.OrdinalIgnoreCase)).OrderBy(t => t.FullName))
        Console.WriteLine(t.FullName);
    return 0;
}

const BindingFlags F = BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static | BindingFlags.DeclaredOnly;
string Vis(bool pub, bool fam) => pub ? "public " : fam ? "protected " : "private ";
var matches = types.Where(t => t.Name == args[0] || t.FullName == args[0]).ToList();
if (matches.Count == 0) { Console.Error.WriteLine($"no type named {args[0]}; try --find"); return 1; }
foreach (var t in matches)
{
    Console.WriteLine($"{t.FullName} : {t.BaseType?.FullName}");
    foreach (var f in t.GetFields(F).OrderBy(f => f.Name))
        Console.WriteLine($"  field  {Vis(f.IsPublic, f.IsFamily)}{(f.IsStatic ? "static " : "")}{f.FieldType.Name} {f.Name}");
    foreach (var p in t.GetProperties(F).OrderBy(p => p.Name))
        Console.WriteLine($"  prop   {p.PropertyType.Name} {p.Name}");
    foreach (var c in t.GetConstructors(F))
        Console.WriteLine($"  ctor   {Vis(c.IsPublic, c.IsFamily)}{t.Name}({string.Join(", ", c.GetParameters().Select(p => p.ParameterType.Name + " " + p.Name))})");
    foreach (var m in t.GetMethods(F).Where(m => !m.IsSpecialName).OrderBy(m => m.Name))
        Console.WriteLine($"  method {Vis(m.IsPublic, m.IsFamily)}{(m.IsVirtual ? "virtual " : "")}{(m.IsStatic ? "static " : "")}{m.ReturnType.Name} {m.Name}({string.Join(", ", m.GetParameters().Select(p => p.ParameterType.Name + " " + p.Name))})");
}
return 0;

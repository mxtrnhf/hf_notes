import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import ghidra.program.model.data.*;
import ghidra.program.model.address.*;
import java.nio.file.*;
import java.util.*;

// Final executed version of the 2026-11-11 1.163 -> 1.151 function port
// (run once with arg "dry", once with arg "real", on /Highfleet.exe.unpacked.exe v1.151).
// Input: /tmp/port163_151/portfuncs.tsv as produced by the dump script + matched.tsv.
public class PortFuncsApply extends GhidraScript {
  DataTypeManager dtm;
  java.util.Map<String,Integer> reasons = new java.util.TreeMap<>();
  void note(String r) { reasons.merge(r, 1, Integer::sum); }

  public void run() throws Exception {
    boolean dry = "dry".equals(getScriptArgs()[0]);
    dtm = currentProgram.getDataTypeManager();
    FunctionManager fm = currentProgram.getFunctionManager();
    List<String> lines = Files.readAllLines(Paths.get("/tmp/port163_151/portfuncs.tsv"));
    int ren = 0, plate = 0, sigMatch = 0, sigDyn = 0;
    int tx = -1;
    boolean commit = false;
    try {
      if (!dry) tx = currentProgram.startTransaction("Port 1.163 function names/plates/sigs");
      for (int li = 0; li < lines.size(); li++) {
        String[] p = lines.get(li).split("\t", -1);
        String a151 = p[1], tier = p[2], name = p[3], ret = p[4], ps = p.length > 5 ? p[5] : "", plateE = p.length > 6 ? p[6] : "";
        Address a = toAddr("0x" + a151);
        Function t = fm.getFunctionAt(a);
        if (t == null) { note("noTargetFn"); continue; }
        String tn = t.getName();
        if (!(tn.startsWith("FUN_") || tn.startsWith("rep_") || tn.startsWith("CFUN_"))) { note("targetAlreadyNamed"); continue; }
        if (dry) ren++;
        else {
          try { t.setName(name, SourceType.USER_DEFINED); ren++; }
          catch (Exception e) { note("renameFail"); continue; }
        }
        String existingPlate = getPlateComment(a);
        if (!plateE.isEmpty() && existingPlate == null) {
          plate++;
          if (!dry) setPlateComment(a, plateE.replace("\\n", "\n").replace("\\t", "\t").replace("\\\\", "\\"));
        } else if (!plateE.isEmpty() && existingPlate != null) note("plateSkipExisting");
        if (ps.contains("USER_DEFINED") || !(ret.startsWith("/undefined") || ret.equals(""))) {
          if (applySigMatched(t, ret, ps, dry)) { sigMatch++; continue; }
          if (tier.equals("hash") && applySigDynamic(t, ret, name, ps, dry)) { sigDyn++; continue; }
          note("sigSkip");
        }
      }
      commit = !dry;
    } finally {
      if (!dry) currentProgram.endTransaction(tx, commit);
    }
    println((dry ? "DRY " : "APPLIED ") + "renamed=" + ren + " plates=" + plate + " sigMatched=" + sigMatch + " sigDynamic=" + sigDyn);
    for (var e : reasons.entrySet()) println("  " + e.getKey() + " = " + e.getValue());
  }

  boolean applySigMatched(Function t, String ret, String ps, boolean dry) {
    String[] params = ps.isEmpty() ? new String[0] : ps.split(";");
    Parameter[] tp = t.getParameters();
    if (params.length == 0 || params.length != tp.length) return false;
    List<Object[]> toApply = new ArrayList<>();
    for (int i = 0; i < params.length; i++) {
      String[] q = params[i].split("&", -1);
      if (q.length < 4) return false;
      if (!q[3].equals("USER_DEFINED")) continue;
      DataType dt = resolveType(q[1]);
      if (dt == null) return false;
      if (!q[2].equals(tp[i].getVariableStorage().toString())) return false;
      if (tp[i].getVariableStorage().size() < dt.getLength()) return false;
      toApply.add(new Object[]{i, dt, q[0]});
    }
    DataType retDt = resolveType(ret);
    if (!ret.startsWith("/undefined") && retDt == null) return false;
    if (dry) return true;
    try {
      if (!ret.startsWith("/undefined")) t.setReturnType(retDt, SourceType.USER_DEFINED);
      for (Object[] o : toApply) {
        tp[(Integer) o[0]].setDataType((DataType) o[1], SourceType.USER_DEFINED);
        tp[(Integer) o[0]].setName((String) o[2], SourceType.USER_DEFINED);
      }
      return true;
    } catch (Exception e) { note("applyMatchFail"); return false; }
  }

  boolean applySigDynamic(Function t, String ret, String fname, String ps, boolean dry) {
    String[] params = ps.isEmpty() ? new String[0] : ps.split(";");
    if (params.length == 0) return false;
    List<Parameter> newParams = new ArrayList<>();
    for (int i = 0; i < params.length; i++) {
      String[] q = params[i].split("&", -1);
      if (q.length < 4) return false;
      DataType dt = resolveType(q[1]);
      if (dt == null) return false;
      SourceType src = q[3].equals("USER_DEFINED") ? SourceType.USER_DEFINED : SourceType.DEFAULT;
      try {
        newParams.add(new ParameterImpl(q[0], dt, i, currentProgram, src));
      } catch (Exception e) { return false; }
    }
    DataType retDt = resolveType(ret);
    if (retDt == null) return false;
    if (dry) return true;
    try {
      t.replaceParameters(newParams, Function.FunctionUpdateType.DYNAMIC_STORAGE_FORMAL_PARAMS, true, SourceType.USER_DEFINED);
      if (!ret.startsWith("/undefined")) t.setReturnType(retDt, SourceType.USER_DEFINED);
      return true;
    } catch (Exception e) { note("applyDynFail " + fname); return false; }
  }

  DataType resolveType(String path) {
    if (path == null || path.isEmpty()) return null;
    try {
      String base = path;
      boolean isPtr = false;
      if (base.endsWith("*")) { isPtr = true; base = base.substring(0, base.length() - 1).trim(); }
      DataType dt = resolveSimple(base);
      if (dt == null) return null;
      if (isPtr) return dtm.resolve(new PointerDataType(dt), DataTypeConflictHandler.KEEP_HANDLER);
      return dt;
    } catch (Exception e) { return null; }
  }

  DataType resolveSimple(String path) {
    String name = path.contains("/") ? path.substring(path.lastIndexOf('/') + 1) : path;
    String cat = path.contains("/") ? path.substring(0, path.lastIndexOf('/')) : "";
    try {
      DataType dt = dtm.getDataType(new CategoryPath(cat), name);
      if (dt != null) return dt;
    } catch (Exception e) {}
    List<DataType> found = new ArrayList<>();
    dtm.findDataTypes(name, found);
    return found.isEmpty() ? null : found.get(0);
  }
}

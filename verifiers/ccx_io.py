"""Read CalculiX output files (.dat first, .frd later) into plain dictionaries."""
import re

_HEADER = re.compile(r"^\s*(displacements|forces) \(\w+,\w+,\w+\) for set (\S+) and time")
_TOTAL = re.compile(r"^\s*total force \(\w+,\w+,\w+\) for set (\S+)")


def _numbers(line):
    """Return all floats of a line if it is purely numeric, else None."""
    try:
        return [float(p) for p in line.split()]
    except ValueError:
        return None


def parse_dat(text):
    """Parse the content of a CalculiX .dat file into plain dicts.

    Structure returned:
        {"sets": {name: {"displacements": {node: [ux, uy, uz]},
                         "forces": {node: [fx, fy, fz]},
                         "total_force": [fx, fy, fz]}}}

    Design rules (lessons from phase 0, encoded):
    - blank lines are structural, never fatal (the FMID trap);
    - unknown blocks are skipped: tolerated, not our business yet;
    - a numeric line outside any block is garbage: raise ValueError
      with line number and content, so callers DETECT, they never guess.
    """
    sets = {}
    state = "outside"
    name, target, total = None, None, None

    for n, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        if line[0].isalpha():                        # header of some block
            m = _TOTAL.match(line)
            if m:
                name = m.group(1)
                total = sets.setdefault(name, {}).setdefault("total_force", [])
                state = "total"
            else:
                m = _HEADER.match(line)
                if m:
                    kind, name = m.groups()
                    target = sets.setdefault(name, {}).setdefault(kind, {})
                    state = kind
                else:
                    state = "unknown"
            continue
        nums = _numbers(line)
        if nums is None:                              # mixed letters+digits: unknown
            state = "unknown"
            continue
        if state in ("displacements", "forces"):
            if len(nums) != 4:
                raise ValueError(f"line {n}: expected 'node ux uy uz', got {line!r}")
            target[int(nums[0])] = nums[1:]
        elif state == "total":
            total.extend(nums)
            state = "unknown"                         # totals are one line
        elif state == "outside":
            raise ValueError(f"line {n}: numeric line outside any block: {line!r}")
        # state "unknown": skipped on purpose
    return {"sets": sets}


def read_dat(path):
    """Parse a CalculiX .dat file from disk."""
    with open(path) as f:
        return parse_dat(f.read())
def parse_frd(text):
    """Parse a CalculiX .frd into plain dicts: node coords + result blocks.

    Returns {"nodes": {node: [x, y, z]},
             "results": {name: {node: [v1, ...]}}}   # e.g. DISP, STRESS, ERROR

    Format lessons from the real phase-0 .frd:
    - fixed-width records with NO separators: ' -1' + id (10 chars) +
      values (12 chars each): fields are SLICED, never split();
    - the '-1' prefix is overloaded THREE ways: node coordinates in the
      mesh section, element records (narrow integer fields), and result
      values inside an open block ('-4' opens, '-3' closes). We try to
      read floats: in the mesh section a failure means "not a coord line"
      (skipped); inside a result block it is real garbage (raise);
    - '-5' lines are component descriptors: skipped.
    """
    nodes = {}
    results = {}
    name = None
    for n, raw in enumerate(text.splitlines(), start=1):
        if raw.startswith(" -4"):
            name = raw[3:13].strip()
            results[name] = {}
        elif name is not None and raw.strip() == "-3":
            name = None
        elif raw.startswith(" -1"):
            node = int(raw[3:13])
            try:
                vals = [float(raw[i:i + 12]) for i in range(13, len(raw), 12)
                        if raw[i:i + 12].strip()]
            except ValueError:
                if name is None:
                    continue          # element record, not node coords: skipped
                raise ValueError(f"frd line {n}: bad value in block {name}: {raw!r}")
            if name is None:
                nodes[node] = vals
            else:
                results[name][node] = vals
        # '-5' descriptors and everything else: skipped
    return {"nodes": nodes, "results": results}


def read_frd(path):
    """Parse a CalculiX .frd file from disk."""
    with open(path) as f:
        return parse_frd(f.read())

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

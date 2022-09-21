import pathlib
import string
import os
import getopt

SUBSTITUTE_CHARS = string.ascii_letters+"_.-$"

def main(args: list[str]) -> int:
  print("ff v1.0")
  print()

  outdir = pathlib.Path(".")

  try:
    opts, a = getopt.getopt(args[1:], "o")
  except getopt.GetoptError:
    print("invalid arguments")
    return 1

  for opt, val in opts:
    if opt == "-o":
      outdir = pathlib.Path(val)

  root = pathlib.Path(".")
  for e in os.walk("."):
    sources = [str(root.joinpath(e[0], f)) for f in e[2] if f.endswith(".ff")]
    consts = {}
    funcs = {}
    tmpls = {}
    for s in sources:
      f, c, t = process(s)
      for name, code in f.items():
        funcs[os.path.join(s.removesuffix(".ff"), name)] = code
      consts |= c
      tmpls |= t
    for name, val in consts.copy().items():
      try:
        newval = substitute(val, consts, tmpls)
      except KeyError as k:
        print(f"Error expanding constant {k.args[0]} in constant {name}.")
        return 1
      else:
        consts[name] = newval
    for name, (args, code) in tmpls.copy().items():
      try:
        inner = consts.copy()
        for arg in args:
          inner[arg] = f"${arg}"
        newcode = substitute(code, inner, tmpls)
      except KeyError as k:
        print(f"Error expanding constant {k.args[0]} in template {name}.")
        return 1
      else:
        tmpls[name] = (args, newcode)
    for name, code in funcs.copy().items():
      try:
        newcode = substitute(code, consts, tmpls)
      except KeyError as k:
        print(f"Error expanding constant {k.args[0]} in function {name}.")
        return 1
      else:
        path = outdir.joinpath(name+".mcfunction")
        if not path.parent.exists():
          path.parent.mkdir()
        print(f"=> {path}")
        mode = "wt"
        if not path.exists():
          mode = "xt"
        with path.open(mode) as f:
          f.write(newcode)

  return 0

def substitute(src: str, consts: dict, tmpls: dict) -> (str, str):
  out = ""
  si = iter(src)
  for ch in si:
    match ch:
      case "$":
        name = ""
        last = ""
        for ch in si:
          if ch not in SUBSTITUTE_CHARS:
            last = ch
            break
          else:
            name += ch
        if name == "$":
          out += "$"
        else:
          out += consts[name]
        out += last
      case "\\":
        name = ""
        for ch in si:
          if ch == "\\":
            name = "\\"
            break
          elif ch == "(":
            break
          else:
            name += ch
        if name == "\\":
          out += "\\"
          continue
        args = []
        arg = ""
        for ch in si:
          if ch == ")":
            args += [arg]
            break
          elif ch == ",":
            args += [arg]
            arg = ""
          else:
            arg += ch
        args = [substitute(a.strip(), consts, tmpls) for a in args]
        tmpl = tmpls[name]
        inner = consts.copy()
        for i, name in enumerate(tmpl[0]):
          inner[name] = args[i]
        out += substitute(tmpl[1], inner, tmpls)
      case _:
        out += ch
  return out

def process(source: str) -> (dict, dict, dict):
  print(source)
  lines = []
  with open(source) as f:
    for no,ln in enumerate(f):
      pln = ln.strip()
      if pln.startswith("#"):
        continue
      pln = pln.translate(str.maketrans("\t\r\n\f\v", "     "))
      while "  " in pln:
        pln = pln.replace("  ", " ")
      if pln == "":
        continue
      lines += [(no, pln, ln)]
  li = iter(lines)
  funcs = dict()
  tmpls = dict()
  consts = dict()
  for no, pln, ln in li:
    match pln.split(" "):
      case ["func", funcname]:
        parsed_func, err = parse_func(li, source.removesuffix(".ff"))
        if err != "":
          print(f"Line {no+1}: Function definition: {err}")
          print(f"  {ln}")
          break
        funcs[funcname] = parsed_func
      case ["const"]:
        parsed_consts, err = parse_const(li)
        if err != "":
          print(f"Line {no+1}: Constant definition: {err}")
          print(f"  {ln}")
          break
        consts |= parsed_consts
      case ["tmpl", tmplname, *args]:
        parsed_tmpl, err = parse_tmpl(li)
        if err != "":
          print(f"Line {no+1}: Function definition: {err}")
          print(f"  {ln}")
          break
        tmpls[tmplname] = (args, parsed_tmpl)
      case [], [""]:
        continue
      case _:
        print(f"Line {no+1}: Invalid syntax")
        print(f"  {ln}")
  return (funcs, consts, tmpls)

def parse_const(li) -> (dict, str):
  out = dict()
  for _, ln, _ in li:
    match ln.split(" "):
      case [constname, "=", *constvalue]:
        out[constname] = " ".join(constvalue)
      case ["end"]:
        return (out, "")
      case []:
        continue
      case _:
        return ({}, "Invalid syntax")

def parse_func(li, ns) -> (str, str):
  lines = []
  for _, ln, _ in li:
    match ln.split(" "):
      case ["end"]:
        return ("\n".join(lines)+"\n", "")
      case ["call", fn]:
        f = fn.split("/")[0] if "/" in fn else ns
        n = fn.split("/")[1] if "/" in fn else fn
        r = pathlib.Path(".").absolute().parent.name
        lines += [f"function {r}:{f}/{n}"]
      case _:
        lines += [ln]

def parse_tmpl(li) -> (str, str):
  lines = []
  for _, ln, _ in li:
    match ln.split(" "):
      case ["end"]:
        return ("\n".join(lines)+"\n", "")
      case _:
        lines += [ln]

if __name__ == "__main__":
  from sys import argv
  main(argv)

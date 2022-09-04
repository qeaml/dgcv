import pathlib
import string
import os
import getopt

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
    for s in sources:
      f, c = process(s)
      for name, code in f.items():
        funcs[os.path.join(s.removesuffix(".ff"), name)] = code
      consts |= c
    for name, val in consts.copy().items():
      try:
        newval = string.Template(val).substitute(consts)
      except KeyError as k:
        print(f"Error expanding constant {k.args[0]} in constant {name}.")
        return 1
      else:
        consts[name] = newval
    for name, code in funcs.copy().items():
      try:
        newcode = string.Template(code).substitute(consts)
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

def process(source: str) -> (dict, dict):
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
  consts = dict()
  while True:
    try:
      no, pln, ln = next(li)
    except StopIteration:
      break
    else:
      match pln.split(" "):
        case ["func", funcname]:
          parsed_func, err = parse_func(li)
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
        case [], [""]:
          continue
        case _:
          print(f"Line {no+1}: Invalid syntax")
          print(f"  {ln}")
  return (funcs, consts)

def parse_const(li) -> (dict, str):
  out = dict()
  while True:
    try:
      _, ln, _ = next(li)
    except StopIteration:
      return ({}, "Unexpected end of input")
    else:
      match ln.split(" "):
        case [constname, "=", *constvalue]:
          out[constname] = " ".join(constvalue)
        case ["end"]:
          return (out, "")
        case []:
          continue
        case _:
          return ({}, "Invalid syntax")

def parse_func(li) -> (str, str):
  lines = []
  while True:
    try:
      _, ln, _ = next(li)
    except StopIteration:
      return ({}, "Unexpected end of input")
    else:
      match ln.split(" "):
        case ["end"]:
          return ("\n".join(lines)+"\n", "")
        case _:
          lines += [ln]

if __name__ == "__main__":
  from sys import argv
  main(argv)

**Moved to [Codeberg](https://codeberg.org/0x4261756D/pdfutil)**

# pdfutil
The original script (merging and rotating) was created in around two hours, information dumping and editing was "ported" from a previous project of mine in another two, so expect ugly code, dumb design decisions and be aware of the Nose Demons (although I doubt anyone will ever use this but who knows)...
I had to merge PDFs and rotate them and somehow writing a python script was faster than finding an existing program doing that...

Version 1.x.x used the [pdfrw](https://github.com/pmaupin/pdfrw) library.
Since that project seems abandoned and does not support all the features I want every later version uses [pypdf](https://github.com/py-pdf/pypdf).

## Dependencies
* Python3 obviously
* [pypdf](https://github.com/py-pdf/pypdf)

## Installation instructions

Install [Python](https://www.python.org/downloads/)
```bash
python3 -m pip install pypdf
```

## Usage
```bash
python3 pdfutil.py -h
```

## Examples

Update the title, author and creation date of *test.pdf*
```bash
python3 pdfutil -i test.pdf --title "Arnold Layne" --author "Syd Barret" --creation_date 19670310004156 -f
```

If against all odds someone really uses this and finds a bug, feel free to report it.
In the even more rare case that you improved something, feel even more free to open a PR.

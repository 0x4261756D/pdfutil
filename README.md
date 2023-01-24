# pdfutil
The original script (merging and rotating) was created in around two hours, information dumping and editing was "ported" from a previous project of mine in another two, so expect ugly code, dumb design decisions and be aware of the Nose Demons (although I doubt anyone will ever use this but who knows)...
I had to merge PDFs and rotate them and somehow writing a python script was faster than finding an existing program doing that...

The way command line arguments are handled is inconsistent and janky.

Expect dates to crumble and not work if you so much as blow on them...

## Dependencies
* Python3 obviously
	* the pip library pdfrw

## Installation instructions

Install [Python](https://www.python.org/downloads/)
```bash
python3 -m pip install pdfrw
```

## Usage
```bash
python3 pdfutil.py -h
```

## Examples

Update the title, author and creation date of *test.pdf*
```bash
python3 pdfutil -i test.pdf --title "Arnold Layne" --author "Syd Barret" --creation_date 19670310 -f
```

If against all odds someone really uses this and finds a bug, feel free to report it.
In the even more rare case that you improved something, feel even more free to open a PR.

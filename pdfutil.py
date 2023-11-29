import pdfrw as pdf # type: ignore
import sys
from os import path

args: list[str] = sys.argv[1:]

def get_out_path() -> str:
	global args
	should_overwrite = "-f" in args or "--force" in args
	if not "-o" in args[:-1]:
		if should_overwrite:
			out_path = args[1]
		else:
			print("no output file provided (-o <output file>)")
			sys.exit(1)
	else:
		out_path = args[args.index("-o") + 1]
	if path.exists(out_path):
		if should_overwrite:
			print("WARNING: Output file already exists, overwriting it.")
		else:
			print("ERROR: Output file already exists, aborting. If you want to overwrite it retry with '-f'")
			sys.exit(1)
	return out_path

def get_info_value(name: str, should_keep: bool, default: str) -> str|None:
	global args
	if f'--{name}' in args[:-1]:
		return args[args.index(f"--{name}") + 1]
	if f'---{name}' in args:
		if should_keep:
			return None
		return default
	if should_keep:
		return default
	return None

def get_info_value_simple(name: str) -> str|None:
	global args
	if f"--{name}" in args[-1]:
		return args[args.index(f"--{name}") + 1]
	return None

def get_datestring(date: str|None) -> str|None:
	if not date:
		return None
	if date[0] == "(":
		date = date[1:]
	if date[-1] == ")":
		date = date[:-1]
	if not date.startswith("D:"):
		date = "D:" + date
	if not (date[-1] == "'" and date[-4] == "'" and date[-7] == "+"):
		date = date + "+00'00'"
	if len(date) != 23:
		print("The provided date", date, "had an incorrect length", len(date), end="")
		date = date[:date.index("+")] + "0" * (23 - len(date)) + date[date.index("+"):]
		print(", it was expanded to", date)
		
	return date

if len(args) < 1 or args[0] in ["-h", "--help"]:
	print("Usage:\n-h, --help: Show this help")
	print("-m, --merge <input files> <-o output file> [-f, --force]: Merges input files into one, overwriting an existing output file if '-f' is provided.")
	print("-r, --rotate <input file> <-o output file> [-f, --force] [--ranges <start> <end> <rotation>... | --rotation <rotation>]: Rotates either the whole input file or every (inclusive) range separately by a multiple of 90 degrees, overwriting an existing output file if '-f' is provided.")
	print("-i, --infos <input file> <-o output file> [-f, --force] [--erase] [--[-]<info> <value>]: Changes the input file's metadata, overwriting an existing output file if '-f' is provided. Missing data is kept as is unless '--erase' is provided, to change the behaviour for a single data point use three dashes instead of two.")
	print("    <info>: author, title, subject, creator, producer, keywords, creation_date, mod_date, page_layout")
	print("        date format: yyyymmddhhmmss+tt'mm', missing data will get filled with '0's, the timezone will be correctly formatted (beware of possibly corrupt dates...).")
	print("        page_layout values: SinglePage, OneColumn, TwoColumnLeft, TwoColumnRight, TwoPageLeft, TwoPageRight")
	print("-di, --dump-infos <file>: Dumps file's metadata")
	print("-d, --delete <input file> <-o output file> [-f, --force] [<page> | <start>-<end> | -<end> | <start>-]...: Deletes the single pages or (inclusive) ranges of pages from the input file, overwriting an existing output file if '-f' is provided")
	sys.exit(0)

if args[0] in ["-di", "--dump-infos"]:
	if len(args) != 2:
		print("ERROR: Too many arguments")
		sys.exit(1)
	if not path.exists(args[1]):
		print(f"ERROR: Input file '{args[1]}' does not exist.")
		sys.exit(1)
	print(pdf.PdfReader(args[1]).Info)
	sys.exit(0)

writer = pdf.PdfWriter()
out_path: str = get_out_path()
if args[0] in ["-m", "--merge"]:
	for arg in args:
		if arg.startswith("-") or arg == out_path:
			continue
		if not path.exists(arg):
			print(f"ERROR: Input file '{arg}' does not exist")
			sys.exit(1)
		reader = pdf.PdfReader(arg)
		writer.addpages(reader.pages)
elif args[0] in ["-r", "--rotate"]:
	if len(args) < 3:
		print("ERROR: Insufficient amount of arguments. Try '-h' for help.")
		sys.exit(1)
	if not path.exists(args[1]):
		print(f"ERROR: Input file '{args[1]}' does not exist.")
		sys.exit(1)
	reader = pdf.PdfReader(args[1])
	pages = reader.pages
	# if there are ranges
	if "--ranges" in args:
		ranges = args[args.index("--ranges")+1:]
		if len(ranges) % 3 != 0:
			print("ERROR: Provided ranges have the wrong number of values.")
			sys.exit(1)
		for i in range(0, len(ranges), 3):
			start: int = int(ranges[i]) - 1
			if start < 0 or start >= len(pages):
				print(f"ERROR: Provided start value '{start}' was outside of the provided file's range '0-{len(pages)}'.")
				sys.exit(1)
			end: int = int(ranges[i + 1])
			if end < 0 or start >= len(pages):
				print(f"ERROR: Provided ending value '{end}' was outside of the provided file's range '0-{len(pages)}'.")
				sys.exit(1)
			if start > end:
				print(f"ERROR: Provided ending value '{end}' is smaller than the provided start value '{start}'.")
				sys.exit(1)
			rotation: int = int(ranges[i + 2])
			if rotation < 0 or rotation % 90 != 0:
				print(f"ERROR: Provided rotation value '{rotation}' is not a positive multiple of 90.")
				sys.exit(1)
			for j in range(start, end):
				pages[j].Rotate = (int(pages[j].inheritable.Rotate or 0) + rotation) % 360
	# if there is only one constant rotation
	else:
		if not "--rotation" in args[:-1]:
			print("ERROR: No rotation provided")
			sys.exit(1)
		rotation: int = int(args[args.index("--rotation") + 1])
		if rotation < 0 or rotation % 90 != 0:
			print(f"ERROR: Provided rotation value '{rotation}' is not a positive multiple of 90.")
			sys.exit(1)
		for j in range(len(pages)):
			pages[j].Rotate = (int(pages[j].inheritable.Rotate or 0) + rotation) % 360
	writer.Info = reader.Info
	writer.addpages(pages)
elif args[0] in ["-i", "--info"]:
	if not path.exists(args[1]):
		print(f"ERROR: Input file '{args[1]}' does not exist.")
		sys.exit(1)
	reader = pdf.PdfReader(args[1])
	writer.addpages(reader.pages)
	should_keep: bool = "--erase" not in args
	author: None|str = get_info_value("author", should_keep, reader.Info.Author) if reader.Info else get_info_value_simple("author")
	title: None|str = get_info_value("title", should_keep, reader.Info.Title) if reader.Info else get_info_value_simple("title")
	subject: None|str = get_info_value("subject", should_keep, reader.Info.Subject) if reader.Info else get_info_value_simple("subject")
	creator: None|str = get_info_value("creator", should_keep, reader.Info.Creator) if reader.Info else get_info_value_simple("creator")
	producer: None|str = get_info_value("producer", should_keep, reader.Info.Producer) if reader.Info else get_info_value_simple("producer")
	mod_date: None|str = get_info_value("mod_date", should_keep, reader.Info.ModDate) if reader.Info else get_info_value_simple("mod_date")
	creation_date: None|str = get_info_value("creation_date", should_keep, reader.Info.CreationDate) if reader.Info else get_info_value_simple("creation_date")
	page_layout: None|str = get_info_value("page_layout", should_keep, reader.Root.PageLayout) if reader.Root else get_info_value_simple("page_layout")

	writer.trailer.Info = pdf.IndirectPdfDict(
		Author = author,
		Title = title,
		Subject = subject,
		Creator = creator,
		Producer = producer,
		ModDate = get_datestring(mod_date),
		CreationDate = get_datestring(creation_date), #"D:" + creation_date + "+00'00'"
	)
	if page_layout != None:
		writer.trailer.Root.PageLayout = pdf.PdfName(page_layout)
elif args[0] in ["-d", "--delete"]:
	# TODO: Make the argument structure more uniform between rotate and delete
	if not path.exists(args[1]):
		print(f"ERROR: Input file '{args[1]}' does not exist.")
		sys.exit(1)
	reader = pdf.PdfReader(args[1])
	pages = reader.pages
	deleted_pages = set()
	start_index = max(args.index('-o') + 1, args.index('-f')) + 1
	for arg in args[start_index:]:
		parts = arg.split('-')
		# single page:
		if len(parts) == 1:
			if not parts[0].isdigit():
				print(f"ERROR: Single page '{parts[0]}' is not a number")
				sys.exit(1)
			page = int(parts[0]) - 1
			if page < 0 or page >= len(pages):
				print(f"ERROR: Single page '{parts[0]}' is outside of the valid range 1-{len(pages)}")
				sys.exit(1)
			deleted_pages.add(page)
		else:
			# no lower bound
			start = 0
			if len(parts[0]) != 0:
				if not parts[0].isdigit():
					print(f"ERROR: Range lower bound '{parts[0]}' is not a number")
					sys.exit(1)
				start = int(parts[0]) - 1
				if start < 0 or start >= len(pages):
					print(f"ERROR: Range lower bound '{parts[0]}' is outside of the valid range 1-{len(pages)}")
					sys.exit(1)
			end = len(pages) - 1
			if len(parts[1]) != 0:
				if not parts[1].isdigit():
					print(f"ERROR: Range upper bound '{parts[1]}' is not a number")
					sys.exit(1)
				end = int(parts[1]) - 1
				if end < 0 or end >= len(pages):
					print(f"ERROR: Range upper bound '{parts[1]}' is outside of the valid range 1-{len(pages)}")
					sys.exit(1)
			print("start", start, "end", end)
			for i in range(start, end + 1):
				deleted_pages.add(i)
	writer.Info = reader.Info
	for i, page in enumerate(reader.pages):
		if not i in deleted_pages:
			writer.addpage(page)
else:
	print("Unrecognized option, try '-h' for help")
	sys.exit(1)

writer.write(out_path)

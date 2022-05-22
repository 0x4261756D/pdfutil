import pdfrw as pdf
import sys
from os import path

args = sys.argv[1:]

def get_out_path():
	global args
	if not "-o" in args[:-1]:
		print("no output file provided (-o <output file>)")
		sys.exit(1)
	out_path = args[args.index("-o") + 1]
	should_overwrite = "-f" in args or "--force" in args
	if path.exists(out_path):
		if should_overwrite:
			print("WARNING: Output file already exists, overwriting it.")
		else:
			print("ERROR: Output file already exists, aborting. If you want to overwrite it retry with '-f'")
			sys.exit(1)
	return out_path

def get_info_value(name, should_keep, default):
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

def get_info_value_simple(name):
	global args
	if f"--{name}" in args[-1]:
		return args[args.index(f"--{name}") + 1]
	return None

if len(args) < 1 or args[0] in ["-h", "--help"]:
	print("Usage:\n-h, --help: Show this help")
	print("-m, --merge <input files> <-o output file> [-f, --force]: Merges input files into one, overwriting an existing output file if '-f' is provided.")
	print("-r, --rotate <input file> <-o output file> [-f, --force] [--ranges <start> <end> <rotation>... | --rotation <rotation>]: Rotates either the whole input file or every range separately by a multiple of 90 degrees, overwriting an existing output file if '-f' is provided.")
	print("-i, --infos <input file> <-o output file> [-f, --force] [--erase] [--[-]<info> <value>]: Changes the input file's metadata, overwriting an existing output file if '-f' is provided. Missing data is kept as is unless '--erase' is provided, to change the behaviour for a single data point use three dashes instead of two.")
	print("    <info>: author, title, subject, creator, producer, keywords, creation_date, mod_date")
	print("        date format: yyyymmddhhmmss, missing data will get filled with '0's (beware of possibly corrupt dates...). Times are always UTC + 0.")
	print("-di, --dump-infos <file>: Dumps file's metadata")
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
out_path = get_out_path()
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
	pages = pdf.PdfReader(args[1]).pages
	# if only one constant rotation is applied
	if "--ranges" in args:
		ranges = args[args.index("--ranges")+1:]
		if len(ranges) % 3 != 0:
			print("ERROR: Provided ranges have the wrong number of values.")
			sys.exit(1)
		for i in range(0, len(ranges), 3):
			start = int(ranges[i]) - 1
			if start < 0 or start >= len(pages):
				print(f"ERROR: Provided start value '{start}' was outside of the provided file's range '0-{len(pages)}'.")
				sys.exit(1)
			end = int(ranges[i + 1])
			if end < 0 or start >= len(pages):
				print(f"ERROR: Provided ending value '{end}' was outside of the provided file's range '0-{len(pages)}'.")
				sys.exit(1)
			if start > end:
				print(f"ERROR: Provided ending value '{end}' is smaller than the provided start value '{start}'.")
				sys.exit(1)
			rotation = int(ranges[i + 2])
			if rotation < 0 or rotation % 90 != 0:
				print(f"ERROR: Provided rotation value '{rotation}' is not a positive multiple of 90.")
				sys.exit(1)
			for j in range(start, end):
				pages[j].Rotate = (int(pages[j].inheritable.Rotate or 0) + rotation) % 360
	else:
		if not "--rotation" in args[:-1]:
			print("ERROR: No rotation provided")
			sys.exit(1)
		rotation = int(args[args.index("--rotation") + 1])
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
	if reader.Info:
		should_keep = "--erase" not in args
		author = get_info_value("author", should_keep, reader.Info.Author)
		title = get_info_value("title", should_keep, reader.Info.Title)
		subject = get_info_value("subject", should_keep, reader.Info.Subject)
		creator = get_info_value("creator", should_keep, reader.Info.Creator)
		producer = get_info_value("producer", should_keep, reader.Info.Producer)
		mod_date = get_info_value("mod_date", should_keep, str(reader.Info.ModDate)[3:-8])
		mod_date += "0" * (14 - len(mod_date))
		creation_date = get_info_value("creation_date", should_keep, str(reader.Info.CreationDate)[3:-8])
		creation_date += "0" * (14 - len(creation_date))
	else:
		author = 	get_info_value_simple("author")
		title = 	get_info_value_simple("title")
		subject = 	get_info_value_simple("subject")
		creator = 	get_info_value_simple("creator")
		producer = 	get_info_value_simple("producer")
		mod_date = 	get_info_value_simple("mod_date")
		creation_date = get_info_value("creation_date")
	writer.trailer.Info = pdf.IndirectPdfDict(
		Author = author,
		Title = title,
		Subject = subject,
		Creator = creator,
		Producer = producer,
		ModDate = "D:" + mod_date + "+00'00'", # get_datestring(mod_date),
		CreationDate = "D:" + creation_date + "+00'00'" # get_datestring(creation_date)
	)
else:
	print("Unrecognized option, try '-h' for help")
	sys.exit(1)

writer.write(out_path)
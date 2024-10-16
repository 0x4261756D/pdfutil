from pypdf import PdfReader, PdfWriter
import sys
from os import path
from datetime import datetime

args: list[str] = sys.argv[1:]

if len(args) < 1 or args[0] in ['-h', '--help']:
	print("Usage:")
	print("-h, --help: Show this help.")
	print("Providing -f or --force overwrites the output file if it already exists and overwrites the input file if no output file is provided.")
	print("-m, --merge <input file>... [-o output file] [-f, --force]: Merges all input files into one.")
	print("-r, --rotate <input file> [-o output file] [-f, --force] [--ranges <start> <end> <rotation>... | --rotation <rotation>]: Rotates either the whole input file or every (inclusive) range separately by a multiple of 90 degrees.")
	print("-i, --infos <input file> [-o output file] [-f, --force] [--erase] [--[-]<info> [<value>]]: Changes the input file's metadata. Missing data is kept as is unless '--erase' is provided, to change the behaviour for a single data point use three dashes instead of two.")
	print("		<info> <string>: author, producer, title, subject, keywords, creator.")
	print("		<info> <yyyymmddhhmmss+ttmm>: creation_date, mod_date. The +ttmm part is time zone info and can be omitted.")
	print("		<info>: hide_toolbar, hide_menubar, hide_windowui, fit_window, center_window, display_doctitle.")
	print("		<info> <[/UseNone, /UseOutlines, /UseThumbs, /UseOC]>: non_fullscreen_pagemode. /UseNone is the default.")
	print("		<info> <[L2R, R2L]>: direction. /L2R is the default.")
	print("-di, --dump-infos <file>: Dumps the input file's metadata.")
	print("-d, --delete <input file> [-o output file] [-f, --force] [--ranges <start> <end>... | --deletion <page>]: Deletes either a single page or every (inclusive) range of the input file.")
	sys.exit(0)

if args[0] in ['-di', '--dump-infos']:
	if len(args) != 2:
		print("ERROR: too many arguments")
		sys.exit(1)
	if not path.exists(args[1]):
		print(f"ERROR: Input file '{args[1]}' does not exist")
		sys.exit(1)
	print(PdfReader(args[1]).metadata)
	sys.exit(0)

should_overwrite = "-f" in args or "--force" in args
if not "-o" in args[:-1]:
	if should_overwrite:
		out_path = args[1]
	else:
		print("ERROR: No output file provided (-o <output file>)")
		sys.exit(1)
else:
	out_path = args[args.index("-o") + 1]
if path.exists(out_path):
	if should_overwrite:
		print("WARNING: Output file already exists, overwriting it.")
	else:
		print("ERROR: Output file already exists, aborting. To overwrite provide '-f'")
		sys.exit(1)
# NOTE: out_path always has a value now

print(out_path)

with PdfWriter() as writer:
	match args[0]:
		case "-m" | "--merge":
			for arg in args:
				if arg.startswith("-") or arg == out_path:
					continue
				if not path.exists(arg):
					print(f"ERROR: Input file '{arg}' does not exist")
					sys.exit(1)
				with open(arg, 'rb') as f:
					writer.append(f)
		case "-r" | "--rotate":
			if len(args) < 3:
				print("ERROR: Insufficient amount of arguments. Try '-h' for help")
				sys.exit(1)
			if not path.exists(args[1]):
				print(f"ERROR: Input file '{args[1]}' does not exist")
				sys.exit(1)
			reader = PdfReader(args[1])
			for page in reader.pages:
				writer.add_page(page)
			if reader.metadata is not None:
				writer.add_metadata(reader.metadata)
			if "--ranges" in args:
				ranges = args[(args.index("--ranges") + 1):]
				if len(ranges) % 3 != 0:
					print("ERROR: Provided ranges have the wrong number of values")
					sys.exit(1)
				for i in range(0, len(ranges), 3):
					start = int(ranges[i]) - 1
					if start < 0 or start >= len(writer.pages):
						print(f"ERROR: Provided start value '{start + 1}' was outside of the file's range (0-{len(writer.pages)})")
						sys.exit(1)
					# NOTE: end does not need a '- 1' because range() is not inclusive for the stop value
					#		e.g. --ranges 1 2 90 would need to rotate page 0 and 1 so range(0, 2) would be correct.
					end = int(ranges[i + 1])
					if end < 0 or end >= len(writer.pages):
						print(f"ERROR: Provided end value '{end}' was outside of the file's range (0-{len(writer.pages)})")
						sys.exit(1)
					rotation = int(ranges[i + 2])
					if rotation < 0 or rotation % 90 != 0:
						print(f"ERROR: Provided rotation value '{rotation}' is not a positive multiple of 90")
						sys.exit(1)
					for j in range(start, end):
						writer.pages[j].rotate(rotation % 360)
			else:
				if not "--rotation" in args[:-1]:
					print("ERROR: No rotation provided")
					sys.exit(1)
				rotation = int(args[args.index("--rotation") + 1])
				if rotation < 0 or rotation % 90 != 0:
					print(f"ERROR: Provided rotation value '{rotation}' is not a positive multiple of 90")
					sys.exit(1)
				for j in range(len(writer.pages)):
					writer.pages[j].rotate(rotation % 360)
		case "-i" | "--info":
			if not path.exists(args[1]):
				print(f"ERROR: Input file '{args[1]}' does not exist")
				sys.exit(1)
			reader = PdfReader(args[1])
			for page in reader.pages:
				writer.add_page(page)
			if reader.metadata is not None and "--erase" not in args:
				writer.add_metadata(reader.metadata)
			if writer.metadata is None:
				writer.add_metadata({})
			assert(writer.metadata is not None)
			if "--author" in args[:-1]:
				if "---author" in args:
					print("WARNING: Ignoring '---author' since '--author' takes precedence")
				writer.add_metadata({"/Author": args[args.index("--author") + 1]})
			elif "---author" in args:
				new_metadata = writer.metadata
				new_metadata.pop("/Author")
				writer.metadata = new_metadata
			if "--producer" in args[:-1]:
				if "---producer" in args:
					print("WARNING: Ignoring '---producer' since '--producer' takes precedence")
				writer.add_metadata({"/Producer": args[args.index("--producer") + 1]})
			elif "---producer" in args:
				new_metadata = writer.metadata
				new_metadata.pop("/Producer")
				writer.metadata = new_metadata
			if "--title" in args[:-1]:
				if "---title" in args:
					print("WARNING: Ignoring '---title' since '--title' takes precedence")
				writer.add_metadata({"/Title": args[args.index("--title") + 1]})
			elif "---title" in args:
				new_metadata = writer.metadata
				new_metadata.pop("/Title")
				writer.metadata = new_metadata
			if "--subject" in args[:-1]:
				if "---subject" in args:
					print("WARNING: Ignoring '---subject' since '--subject' takes precedence")
				writer.add_metadata({"/Subject": args[args.index("--subject") + 1]})
			elif "---subject" in args:
				new_metadata = writer.metadata
				new_metadata.pop("/Subject")
				writer.metadata = new_metadata
			if "--keywords" in args[:-1]:
				if "---keywords" in args:
					print("WARNING: Ignoring '---keywords' since '--keywords' takes precedence")
				writer.add_metadata({"/Keywords": args[args.index("--keywords") + 1]})
			elif "---keywords" in args:
				new_metadata = writer.metadata
				new_metadata.pop("/Keywords")
				writer.metadata = new_metadata
			if "--creator" in args[:-1]:
				if "---creator" in args:
					print("WARNING: Ignoring '---creator' since '--creator' takes precedence")
				writer.add_metadata({"/Creator": args[args.index("--creator") + 1]})
			elif "---creator" in args:
				new_metadata = writer.metadata
				new_metadata.pop("/Creator")
				writer.metadata = new_metadata
			if "--creation_date" in args[:-1]:
				if "---creation_date" in args:
					print("WARNING: Ignoring '---creation_date' since '--creation_date' takes precedence")
				writer.add_metadata({"/CreationDate": "D\072" + datetime.strptime(args[args.index("--creation_date") + 1], "%Y%m%d%H%M%S%z").strftime("%Y%m%d%H%M%S%:z").replace(":", "'")})
			elif "---creation_date" in args:
				new_metadata = writer.metadata
				new_metadata.pop("/CreationDate")
				writer.metadata = new_metadata
			if "--mod_date" in args[:-1]:
				if "---mod_date" in args:
					print("WARNING: Ignoring '---mod_date' since '--mod_date' takes precedence")
				writer.add_metadata({"/ModDate": "D\072" + datetime.strptime(args[args.index("--mod_date") + 1], "%Y%m%d%H%M%S%z").strftime("%Y%m%d%H%M%S%:z")})
			elif "---mod_date" in args:
				new_metadata = writer.metadata
				new_metadata.pop("/ModDate")
				writer.metadata = new_metadata
			if "--hide_toolbar" in args:
				if "---hide_toolbar" in args:
					print("WARNING: Ignoring '---hide_toolbar' since '--hide_toolbar' takes precedence")
				if writer.viewer_preferences is None:
					writer.create_viewer_preferences()
				assert(writer.viewer_preferences is not None)
				writer.viewer_preferences.hide_toolbar = True
			elif "---hide_toolbar" in args:
				if writer.viewer_preferences is None:
					writer.create_viewer_preferences()
				assert(writer.viewer_preferences is not None)
				writer.viewer_preferences.hide_toolbar = False
			if "--hide_menubar" in args:
				if "---hide_menubar" in args:
					print("WARNING: Ignoring '---hide_menubar' since '--hide_menubar' takes precedence")
				if writer.viewer_preferences is None:
					writer.create_viewer_preferences()
				assert(writer.viewer_preferences is not None)
				writer.viewer_preferences.hide_menubar = True
			elif "---hide_menubar" in args:
				if writer.viewer_preferences is None:
					writer.create_viewer_preferences()
				assert(writer.viewer_preferences is not None)
				writer.viewer_preferences.hide_menubar = False
			if "--hide_windowui" in args:
				if "---hide_windowui" in args:
					print("WARNING: Ignoring '---hide_windowui' since '--hide_windowui' takes precedence")
				if writer.viewer_preferences is None:
					writer.create_viewer_preferences()
				assert(writer.viewer_preferences is not None)
				writer.viewer_preferences.hide_windowui = True
			elif "---hide_windowui" in args:
				if writer.viewer_preferences is None:
					writer.create_viewer_preferences()
				assert(writer.viewer_preferences is not None)
				writer.viewer_preferences.hide_windowui = False
			if "--fit_window" in args:
				if "---fit_window" in args:
					print("WARNING: Ignoring '---fit_window' since '--fit_window' takes precedence")
				if writer.viewer_preferences is None:
					writer.create_viewer_preferences()
				assert(writer.viewer_preferences is not None)
				writer.viewer_preferences.fit_window = True
			elif "---fit_window" in args:
				if writer.viewer_preferences is None:
					writer.create_viewer_preferences()
				assert(writer.viewer_preferences is not None)
				writer.viewer_preferences.fit_window = False
			if "--center_window" in args:
				if "---center_window" in args:
					print("WARNING: Ignoring '---center_window' since '--center_window' takes precedence")
				if writer.viewer_preferences is None:
					writer.create_viewer_preferences()
				assert(writer.viewer_preferences is not None)
				writer.viewer_preferences.center_window = True
			elif "---center_window" in args:
				if writer.viewer_preferences is None:
					writer.create_viewer_preferences()
				assert(writer.viewer_preferences is not None)
				writer.viewer_preferences.center_window = False
			if "--display_doctitle" in args:
				if "---display_doctitle" in args:
					print("WARNING: Ignoring '---display_doctitle' since '--display_doctitle' takes precedence")
				if writer.viewer_preferences is None:
					writer.create_viewer_preferences()
				assert(writer.viewer_preferences is not None)
				writer.viewer_preferences.display_doctitle = True
			elif "---display_doctitle" in args:
				if writer.viewer_preferences is None:
					writer.create_viewer_preferences()
				assert(writer.viewer_preferences is not None)
				writer.viewer_preferences.display_doctitle = False
			if "--non_fullscreen_pagemode" in args[:-1]:
				if "---non_fullscreen_pagemode" in args:
					print("WARNING: Ignoring '---non_fullscreen_pagemode' since '--non_fullscreen_pagemode' takes precedence")
				if writer.viewer_preferences is None:
					writer.create_viewer_preferences()
				mode = args[args.index("--non_fullscreen_pagemode")]
				allowed_pagemodes = ["/UseNone", "/UseOutlines", "/UseThumbs", "/UseOC"]
				if mode not in allowed_pagemodes:
					print(f"ERROR: Unknown non_fullscreen_pagemode '{mode}', should be one of {allowed_pagemodes}")
					sys.exit(1)
				assert(writer.viewer_preferences is not None)
				writer.viewer_preferences.non_fullscreen_pagemode = mode
			elif "---non_fullscreen_pagemode" in args:
				if writer.viewer_preferences is None:
					writer.create_viewer_preferences()
				assert(writer.viewer_preferences is not None)
				writer.viewer_preferences.non_fullscreen_pagemode = "/UseNone"
			if "--direction" in args[:-1]:
				if "---direction" in args:
					print("WARNING: Ignoring '---direction' since '--direction' takes precedence")
				if writer.viewer_preferences is None:
					writer.create_viewer_preferences()
				direction = args[args.index("--direction")]
				allowed_directions = ["/L2R", "/R2L"]
				if direction not in allowed_directions:
					print(f"ERROR: Unknown direction '{direction}', should be one of {allowed_directions}")
					sys.exit(1)
				assert(writer.viewer_preferences is not None)
				writer.viewer_preferences.direction = direction
			elif "---direction" in args:
				if writer.viewer_preferences is None:
					writer.create_viewer_preferences()
				assert(writer.viewer_preferences is not None)
				writer.viewer_preferences.direction = "/L2R"
			# TODO: Add other viewer preferences
		case "-d" | "--delete":
			if len(args) < 3:
				print("ERROR: Insufficient amount of arguments. Try '-h' for help")
				sys.exit(1)
			if not path.exists(args[1]):
				print(f"ERROR: Input file '{args[1]}' does not exist")
				sys.exit(1)
			reader = PdfReader(args[1])
			for page in reader.pages:
				writer.add_page(page)
			if reader.metadata is not None:
				writer.add_metadata(reader.metadata)
			if "--ranges" in args:
				bit_set = [False for i in range(len(writer.pages))]
				ranges = args[(args.index("--ranges") + 1):]
				if len(ranges) % 2 != 0:
					print("ERROR: Provided ranges have the wrong number of values")
					sys.exit(1)
				for i in range(0, len(ranges), 2):
					start = int(ranges[i]) - 1
					if start < 0 or start >= len(writer.pages):
						print(f"ERROR: Provided start value '{start + 1}' was outside of the file's range (0-{len(writer.pages)})")
						sys.exit(1)
					# NOTE: end does not need a '- 1' because range() is not inclusive for the stop value
					#		e.g. --ranges 1 2 90 would need to rotate page 0 and 1 so range(0, 2) would be correct.
					end = int(ranges[i + 1])
					if end < 0 or end >= len(writer.pages):
						print(f"ERROR: Provided end value '{end}' was outside of the file's range (0-{len(writer.pages)})")
						sys.exit(1)
					for j in range(start, end):
						bit_set[j] = True
				for i in reversed(range(len(writer.pages))):
					if bit_set[i]:
						writer.remove_page(i)
			else:
				if not "--deletion" in args[:-1]:
					print("ERROR: No rotation provided")
					sys.exit(1)
				writer.remove_page(int(args[args.index("--deletion") + 1]) - 1)
		case _:
			print(f"ERROR: Unknown command '{args[0]}'. Try '-h' for help")
	with open(out_path, 'wb') as f:
		writer.write(f)
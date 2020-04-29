
import requests
import sys
import re
import json
import datetime
from bs4 import BeautifulSoup
import codecs
import random
import os
import glob
######################GLOBAL#######################
verbose = True
SEP = "-"*10
BOHOOR = {
	"الطويل",
	"المديد",
	"البسيط",
	"الوافر",
	"الكامل",
	"الهزج",
	"الرجز",
	"الرمل",
	"السريع",
	"المنسرح",
	"الخفيف",
	"المقتضب",
	"المجتث",
	"المتقارب"
}
class Poem:
	def __init__(self,text,sea):
		self._text = text
		lines = text.splitlines()
		self._abyat = ["   ".join(lines[i:i+2]) for i in range(0,len(lines),2)]
		self._sea = sea
	def __len__(self):
		return len(self._abyat)
	def __str__(self):
		return self._text

######################UTILS########################
def request_html(link):
	try:
		response = requests.get(link, timeout=5)
		if response:
			html = response.content
			return html.decode("windows-1256", errors='ignore')
		else:
			return None
	except:
		return None
#--------------------------------------------------
def load_json(json_file_name):
    config = None
    try:
        f = open(json_file_name)
        string = f.read()
        # remove comments and tabs
        string = re.sub(re.compile("//.*?\n" ), "", string)
        string = string.replace("\t"," ")
        # load python object
        config = json.loads(string)
        f.close()
    except e:
        print(e)
        raise
    return config
#--------------------------------------------------
def load_poem_file(poem_file):
	poems = []
	with codecs.open(poem_file,"r","utf-8") as f:
		poems_text = f.read().split(SEP)
		for p in poems_text:
			lines = p.strip().splitlines()
			if len(lines)<2:
				continue
			sea = lines[0]
			text = "\n".join(lines[1:])
			poems.append(Poem(text,sea))
	return poems
######################CORE#########################
#-------------------DIWAN--------------------------
DIWAN_ROOT = "https://www.aldiwan.net/"
def diwan_parse_poem(html):
	poem,sea = None,None
	try:
		soup = BeautifulSoup(html)
		selector_path = "html body div.container.m-section-1 div div.col-sm-7.col-xs-12.pull-right.text-center div div"
		poem_div = soup.select(selector_path)[0]
		poem = poem_div.text.strip()
		sea_path="body > div.container.m-section-1 > div > div.col-sm-5.col-xs-12.pull-left > div:nth-child(2) > h4 > a:nth-child(8)"
		sea_div = soup.select(sea_path)[0]
		sea = sea_div.text.replace("بحر ","").split()[-1]
	except:
		pass
	return poem,sea
def diwan_compile_poem(**args):
	SourceRoot = args["Source"]
	CompileFrom = args.get("From",-1)
	CompileTo = args.get("To",-1)
	SaveTo = args["SaveTo"]

	#<-
	if verbose:
		print ("\t\tCompiling poems from %d to %d" % (CompileFrom,CompileTo))
		print ("\t\tSource: %s" % SourceRoot)
		print ("\t\tWriting in: %s" % SaveTo)
	#->

	toFile = codecs.open(SaveTo,"a","utf-8")

	if CompileFrom != -1:
		CompileToInclusive = CompileTo + 1 # inclusive
		files = ["%s/poem%d.html" % (SourceRoot,i) for i in range(CompileFrom,CompileToInclusive) if os.path.exists("%s/poem%d.html")]
	else:
		files = glob.glob("%s/poem*.html" % SourceRoot)				


	for i,filename in enumerate(files):

		#<-
		if verbose:
			print ("\t\tPoem: %d/%d" % (i,len(files)))
		#->

		with codecs.open(filename,"r","windows-1256") as f:
			html = f.read()

		poem,sea = diwan_parse_poem(html)
		if not poem:
			continue
		#print("%s\n%s\n%s\n" % (sea,poem,SEP))

		toFile.write("%s\n%s\n%s\n" % (sea,poem,SEP))

	toFile.close()
def diwan_scrape_poem(**args):
	ScrapeFrom = args["From"]
	ScrapeTo = args["To"]
	SaveTo = args["SaveTo"]
	Sample = args.get("Sample",None)

	

	ScrapeToInclusive = ScrapeTo + 1 # inclusive
	inP = list(range(ScrapeFrom,ScrapeToInclusive))
	if Sample:
		inP = random.sample(inP, Sample)

		#<-
		if verbose:
			print ("\t\tScrapeing %d sample poems from %d to %d" % (Sample,ScrapeFrom,ScrapeTo))
		#->

	else: 

		#<-
		if verbose:
			print ("\t\tScrapeing poems from %d to %d" % (ScrapeFrom,ScrapeTo))
		#->

	for i,index in enumerate(inP):

		#<-
		if verbose:
			print ("\t\tPoem: %d/%d" % (i,len(inP)))
		#->

		link = "%spoem%d.html" % (DIWAN_ROOT,index)
		html = request_html(link)
		if not html:
			continue

		with codecs.open("%s/poem%d.html" % (SaveTo,index),"w","windows-1256") as f:
			f.write(html)
def diwan_scrape(**args):
	Targets = {"poems": diwan_scrape_poem}
	ScrapeTarget = args["Target"]

	#<-
	if verbose:
		print ("\tDiwan %s" % ScrapeTarget)
	#->

	Targets[ScrapeTarget](**args)
def diwan_compile(**args):
	Targets = {"poems": diwan_compile_poem}
	CompileTarget = args["Target"]

	#<-
	if verbose:
		print ("\tDiwan %s" % CompileTarget)
	#->

	Targets[CompileTarget](**args)
#--------------------------------------------------
#-------------------Sampling-----------------------
def random_sample(**args):
	SampleFrom = args["From"]
	NumberOfSamples = args["Samples"]
	SamplePadding  = args["Padding"]
	SaveTo = args["SaveTo"]

	#<-
	if verbose:
		print ("Sampling %d from %s randomly" % (NumberOfSamples,SampleFrom))
	#->

	poems = load_poem_file(SampleFrom)
	allabyats = []
	for p in poems: 
		allabyats += [(b,p._sea) for b in p._abyat]

	data = {}
	sample = random.sample(allabyats, NumberOfSamples)
	for i,s in enumerate(sample):
		data["%s" % str(i).zfill(SamplePadding)] = {"bayt": s[0],"bahar":s[1]}

	with codecs.open(SaveTo,"w","utf-8") as f:
		f.write(json.dumps(data,indent=4,sort_keys=True, ensure_ascii=False))
def bahar_uniform_sample(**args):
	SampleFrom = args["From"]
	NumberOfSamples = args["Samples"]
	SamplePadding  = args["Padding"]
	SaveTo = args["SaveTo"]
	
	#<-
	if verbose:
		print ("Sampling %d from %s with sea uniform" % (NumberOfSamples,SampleFrom))
	#->

	poems = load_poem_file(SampleFrom)
	allabyats = {b:[] for b in BOHOOR}
	for p in poems:
		if p._sea in allabyats:
			allabyats[p._sea] += p._abyat

	bohoorLen = [(k,len(v)) for k,v in allabyats.items()]
	minBahar = min([l for b,l in bohoorLen])
	
	#<-
	if verbose:
		print ("Current distribution:")
		for k,v in bohoorLen:
			print(f"{k}:{v}")
	#->
	
	if minBahar == 0:
		print("No enough data for all bohoor")
		return

	toSample = min(NumberOfSamples,minBahar)
	samples = {k: random.sample(v, toSample) for k,v in allabyats.items()}

	data = {}
	count = 0
	for k,v in samples.items():
		for b in v:
			data["%s" % str(count).zfill(SamplePadding)] = {"bayt": b,"bahar":k}
			count += 1

	with codecs.open(SaveTo,"w","utf-8") as f:
		f.write(json.dumps(data,indent=4,sort_keys=True, ensure_ascii=False))
######################GATE#########################
def scrape_(**args):
	scrape_functions = {
	"diwan": diwan_scrape
	}

	ScrapeWhat = args["What"] 

	#<-
	if verbose:
		print ("Scrapeing %s" % ScrapeWhat)
	#->

	scrape_functions[ScrapeWhat](**args)
#--------------------------------------------------
def compile_(**args):
	compile_functions = {
	"diwan": diwan_compile
	}

	CompileWhat = args["What"] 

	#<-
	if verbose:
		print ("Compiling %s" % CompileWhat)
	#->

	compile_functions[CompileWhat](**args)
#--------------------------------------------------
def sample_(**args):
	sample_functions = {
	"random": random_sample,
	"bahar_uniform": bahar_uniform_sample
	}

	SamplingMethod = args["Method"]
	 

	#<-
	if verbose:
		print ("Sampling %s" % SamplingMethod)
	#->

	sample_functions[SamplingMethod](**args)

######################MAIN#########################
if __name__ == '__main__':
	if len(sys.argv) <= 1:
		print ('no config file provided')
		exit()
	argv = sys.argv
	argv.pop(0)

	pipelineFile = argv.pop(0)
	pipeline = load_json(pipelineFile)

	functions = {
	    "scrape": scrape_,
	    "compile": compile_,
	    "sample": sample_
	}

	for stage in pipeline["Pipeline"]:
		cmd = stage["CMD"]
		print (datetime.datetime.now())
		functions[cmd](**stage)
		print (datetime.datetime.now())


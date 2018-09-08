#!/usr/bin/env python3

# The MIT License (MIT)
# Copyright (c) 2018 Esukhia
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
# OR OTHER DEALINGS IN THE SOFTWARE.

import re
import os
import glob

PAREN_RE = re.compile(r"\(([^\),]*),([^\),]*)\)")

def parrepl(match, mode, pagelinenum, filelinenum, volnum, shortfilename):
    first = match.group(1)
    sec = match.group(2)
    if (len(first) > 0 and len(sec) > 0 and (
            (first[0]== '་' and sec[0]!= '་') or 
            (sec[0]== '་' and first[0]!= '་') or
            (first[-1]== '་' and sec[-1]!= '་') or
            (sec[-1]== '་' and first[-1]!= '་'))):
        report_error(pagelinenum, filelinenum, volnum, shortfilename, "format", "༺ཚེག་དང་གུག་རྟགས་མི་འགྲིག་པ།༻ tsheg not matching in parenthesis", "")
    return mode == 'first' and first or sec

error_regexps = [
        {"reg": re.compile(r"([^ །\(\)\[,]།[^ །\(\]\)༽,n]|(?:[^ངོེིུྃཾ]|ང[^ངོེིུྃཾ]|[^ང][ོེིུྃཾ])་།|(?:[^ཀགཤ།ོེིུྃཾ]|[ཀགཤ][^ཀགཤོེིུྃཾ]|[^ཀགཤ][ོེིུྃཾ]|[ཀགཤ][ོེིུྃཾ]།+)། །།|།།།)"), "msg": "༺ཚེག་ཤད་མི་འགྲིག་པ།༻ invalid shad sequence", "type": "punctuation"},
        {"reg": re.compile(r"[^ཀ-ྼ][ཱ-྄྆྇ྍ-ྼ]"), "msg": "༺ཁྲིམས་འགལ་ཡི་གེ།༻ invalid unicode combination sequence", "type": "invalid"},
        {"reg": re.compile(r"([^༄༅]༅|[^࿓࿔]࿔|[࿔༅][^།༅࿔])"), "msg": "༺ཡིག་མགོ་ཁྲིམས་འགལ།༻ invalid yigo", "type": "punctuation"},
        {"reg": re.compile(r"[^ༀ-࿚#-~ \[\]\{\}\.ऽ।ं]"), "msg": "༺བོད་ཡིན་མིན་པ།༻ invalid unicode characters (non-Tibetan, non-ascii)", "type": "invalid"},
        {"reg": re.compile(r"([ྱུྲཿཾ྄ྃྭིྀ་ ])\1"), "msg": "༺དབྱངས་ཀྱི་སྐྱོན།༻ invalid double diactitic sign (shabkyu, gigu, etc.)", "type": "invalid"},
        {"reg": re.compile(r"[ༀ-༃༆-༊༎-༟ྰ]"), "msg": "༺ཡི་གེའི་དོགས་གཞི།༻ suspicious Tibetan character (mind 0FB0 vs. 0F71)", "type": "invalid"},
        {"reg": re.compile(r"([ཱ-྇][ྍ-ྼ]|[ི-྄]ཱ|[ྃཾཿ][ཱ-ཽྀ])"), "msg": "༺ཡི་གེ་གོ་རིམ་མི་འགྲིག་པ།༻ invalid character order (vowel before subscript)", "type": "invalid"},
        {"reg": re.compile(r"(ཪ[ླྙྲྱཱ-྇ །་༼-ྌྉྈ\(\)\[\]]|[^ཏ]ྲ[ྐ-ྫྷྮ-ྻ])"), "msg": "༺ར་མགོ་སྐྱོན་ཅན་གྱི་དོགས་གཞི།༻ possible wrong form of rago used (0F62 vs. 0F65)", "type": "invalid"},
        {"reg": re.compile(r"([ཀགཤ།] །|[^ ཀགཤ།]། |[ཀགཤ།]། |[ཀགཤ།][། ]|[༽ཿ་ \]nl])$"), "msg": "༺ཐིག་འཕྲེང་མཇུག་མཐའ་སྐྱོན་ཅན།༻ invalid end of line", "type": "punctuation", "neg": True},
        {"reg": re.compile(r"([ཱེཻོཽ])\1"), "msg": "༺དབྱངས་ཀྱི་སྐྱོན།༻ invalid vowel duplication (use 0F7D and 0F7B when relevant)", "type": "invalid"},
        {"reg": re.compile(r"ཿ་"), "msg": "༺རྣམ་བཅད་མཐར་ཚེག་བཀོད་པའི་སྐྱོན།༻ invalid visarga + tshek", "type": "punctuation"},
    ]

def check_simple_regexp(line, pagelinenum, filelinenum, volnum, options, shortfilename):
    for regex_info in error_regexps:
        if "neg" in regex_info and regex_info["reg"]:
            if not regex_info["reg"].search(line):
                report_error(pagelinenum, filelinenum, volnum, shortfilename, regex_info["type"], regex_info["msg"], "")
            continue
        for match in regex_info["reg"].finditer(line):
            s = match.start()
            e = match.end()
            linewithhighlight = line[:s]+"**"+line[s:e]+"**"+line[e:]
            report_error(pagelinenum, filelinenum, volnum, shortfilename, regex_info["type"], regex_info["msg"], linewithhighlight)

def report_error(linestr, filelinenum, volnum, shortfilename, errortype, errorstr, linewithhighlight):
    printerror(shortfilename+", l. "+str(filelinenum)+" ("+linestr+"): "+errortype+": "+errorstr)
    if len(linewithhighlight) > 1:
        printerror("  -> "+linewithhighlight)

def endofverse(line, endidx, state, volnum, shortfilename):
    nbsyls = state['curnbsyllables']
    #print(str(nbsyls)+" "+str(state['prevnbsyllables']))
    if state['prevnbsyllables'] == 7:
        if nbsyls == 6 or nbsyls == 8:
            bchar = state['curbeginchar']
            line = state['curbeginline']
            highlight = line[:bchar]+"***"+line[bchar:]
            report_error(state['curbeginpagelinenum'], state['curbeginfilelinenum'], volnum, shortfilename, "verses", "verse has "+str(nbsyls)+" syllables while previous one has 7", highlight)
    state['prevnbsyllables'] = nbsyls
    state['curbeginchar'] = -1

def endofsyllable(line, endidx, state):
    syllable = line[state['curbeginsylchar']:state['curendsylchar']]
    if syllable in ['བཛྲ', 'པདྨ', 'པདྨའི', 'སིདྡྷི', 'པའམ', 'ཀརྨ']:
        state['curnbsyllables'] += 1
    if syllable.endswith('འོ'):
        state['curnbsyllables'] += 1
    state['curnbsyllables'] += 1

def check_verses(line, pagelinenum, filelinenum, state, volnum, options, shortfilename):
    lastistshek = False
    lastisbreak = False
    for idx in range(1,len(line)):
        c = line[idx]
        if c in "#\{\}[]T01234567890ab.":
            continue
        if (c >= 'ཀ' and c <= 'ྃ') or (c >= 'ྐ' and c <= 'ྼ'):
            if state['curbeginchar'] == -1:
                state['curbeginchar'] = idx
                state['curnbsyllables'] = 0
                state['curbeginpagelinenum'] = pagelinenum
                state['curbeginline'] = line
                state['curbeginfilelinenum'] = filelinenum
            if lastistshek == False and lastisbreak == False:
                continue
            if not lastisbreak:
                endofsyllable(line, idx-1, state)
            lastisbreak = False
            state['curbeginsylchar'] = idx
            lastistshek = False
        elif c == '་' and not lastistshek and not lastisbreak:
            state['curendsylchar'] = idx
            lastistshek = True
            lastisbreak = False
        elif not lastisbreak:
            state['curendsylchar'] = idx
            finalidx = idx-2 if lastistshek else idx-1
            endofsyllable(line, finalidx, state)
            endofverse(line, finalidx, state, volnum, shortfilename)
            lastisbreak = True

def parse_one_line(line, filelinenum, state, volnum, options, shortfilename):
    if filelinenum == 1:
        state['pageseqnum']= 1
        state['pagenum']= 1
        state['pageside']= 'a'
        return
    pagelinenum = ''
    endpnumi = line.find(']')
    if endpnumi == -1:
        report_error("", filelinenum, volnum, shortfilename, "format", "cannot find \"]\"", "")
        return
    pagelinenum = line[1:endpnumi]
    if len(pagelinenum) < 2:
        report_error("", filelinenum, volnum, shortfilename, "format", "cannot understand page indication \"["+pagelinenum+"]\"", "")
        return
    pagenum = -1
    pageside = -1
    linenum = 0
    isBis = False
    doti = pagelinenum.find('.')
    if doti == -1:
        pageside = pagelinenum[-1]
        if pageside not in ['a', 'b']:
            report_error(pagelinenum, filelinenum, volnum, shortfilename, "format", "cannot understand page side", "")
            return
        pagenumstr = pagelinenum[:-1]
        if pagelinenum[-2]== 'x':
            isBis = True
            pagenumstr = pagelinenum[:-2]
        try:
            pagenum = int(pagenumstr)
        except ValueError:
            report_error(pagelinenum, filelinenum, volnum, shortfilename, "format", "cannot convert page to integer", "")
            return
    else:
        linenumstr = pagelinenum[doti+1:]
        pageside = pagelinenum[doti-1]
        if pageside not in ['a', 'b']:
            report_error(pagelinenum, filelinenum, volnum, shortfilename, "format", "cannot understand page side", "")
            return
        pagenumstr = pagelinenum[0:doti-1]
        if pagelinenum[doti-2]== 'x':
            isBis = True
            pagenumstr = pagelinenum[0:doti-2]
        try: 
            pagenum = int(pagenumstr)
            linenum = int(linenumstr)
        except ValueError:
            report_error(pagelinenum, filelinenum, volnum, shortfilename, "format", "cannot convert page / line to integer", "")
            return
    newpage = False
    if 'pagenum' in state and 'pageside' in state:
        oldpagenum = state['pagenum']
        oldpageside = state['pageside']
        if oldpagenum != pagenum and oldpagenum != pagenum-1:
            report_error("", filelinenum, volnum, shortfilename, "pagenumbering", "༺ཤོག་གྲངས་ཀྱི་སྐྱོན།༻ leap in page numbers from "+str(oldpagenum)+" to "+str(pagenum), "")
        if oldpagenum == pagenum and oldpageside == 'b' and pageside == 'a':
            report_error("", filelinenum, volnum, shortfilename, "pagenumbering", "༺ཤོག་ངོའི་སྐྱོན།༻ going backward in page sides", "")
        if oldpagenum == pagenum-1 and (pageside == 'b' or oldpageside == 'a'):
            report_error("", filelinenum, volnum, shortfilename, "pagenumbering", "༺ཤོག་ངོའི་སྐྱོན།༻ leap in page sides", "")
        if oldpagenum != pagenum or oldpageside != pageside:
            newpage = True
    if newpage:
        state['pageseqnum']+= 1
    state['pagenum']= pagenum
    state['pageside']= pageside
    if 'linenum' in state and linenum != 0:
        oldlinenum = state['linenum']
        if oldlinenum != linenum and oldlinenum != linenum-1:
            report_error(pagelinenum, filelinenum, volnum, shortfilename, "pagenumbering", "༺ཐིག་གྲངས་ཀྱི་སྐྱོན།༻ leap in line numbers from "+str(oldlinenum)+" to "+str(linenum), "")
    state['linenum']= linenum
    check_simple_regexp(line, pagelinenum, filelinenum, volnum, options, shortfilename)
    #check_verses(line, pagelinenum, filelinenum, state, volnum, options, shortfilename)
    text = ''
    if len(line) > endpnumi+1:
        text = line[endpnumi+1:]
        if '{T' in text:
            if not '}' in text:
                report_error(pagelinenum, filelinenum, volnum, shortfilename, "format", "missing closing \"}\"", "")
            closeidx = text.find('}')
            if not text.startswith('༄༅༅། །', closeidx+1) and not text.startswith('༄༅། །', closeidx+1) and not text.startswith('༄། །', closeidx+1):
                rightcontext = text[closeidx+1:closeidx+5]
                report_error(pagelinenum, filelinenum, volnum, shortfilename, "punctuation", "༺དབུ་འཁྱུད་ཆད་པའི་སྐྱོན།༻ possible wrong beginning of text: \""+rightcontext+"\" should be \"༄༅༅། །\", \"༄༅། །\" or \"༄། །\"", "")
            locstr = str(pagenum)+pageside+str(linenum)+" ("+str(volnum)+")"
        if 'keep_errors_indications' not in options or not options['keep_errors_indications']:
            text = text.replace('[', '').replace(']', '')
        if 'fix_errors' not in options or not options['fix_errors']:
            text = re.sub(r"\(([^\),]*),([^\),]*)\)", lambda m: parrepl(m, 'first', pagelinenum, filelinenum, volnum, shortfilename), text)
        else:
            text = re.sub(r"\(([^\),]*),([^\),]*)\)", lambda m: parrepl(m, 'second', pagelinenum, filelinenum, volnum, shortfilename), text)
        if text.find('(') != -1 or text.find(')') != -1:
            report_error(pagelinenum, filelinenum, volnum, shortfilename, "format", "༺གུག་རྟགས་ཆད་པའི་སྐྱོན།༻ spurious parenthesis", "")

def parse_one_file(infilename, volnum, options, shortfilename):
    with open(infilename, 'r', encoding="utf-8") as inf:
        state = {
            "curnbsyllables": 0,
            "prevnbsyllables": 0,
            "curbeginpagelinenum": "",
            "curbeginline": "",
            "curbeginchar": -1,
            "curbeginsylchar": -1,
            "curbeginfilelinenum": 0,
            "curendsylchar": -1,
        }
        linenum = 1
        for line in inf:
            if linenum == 1:
                line = line[1:]# remove BOM
            # [:-1]to remove final line break
            parse_one_line(line[:-1], linenum, state, volnum, options, shortfilename)
            linenum += 1

errfile = open("errors.txt","w", encoding="utf-8")

def printerror(err):
    errfile.write(err+"\n")

if __name__ == '__main__':
    """ Example use """
    options = {
        "fix_errors": False,
        "keep_errors_indications": False
    }
    for infilename in sorted(glob.glob("../derge-tengyur-tags/*.txt")):
        #print(infilename)
        volnum = infilename[22:25]
        shortfilename = infilename[22:-4]
        try:
            volnum = int(volnum)
        except ValueError:
            print('wrong file format: '+shortfilename+'.txt')
            continue
        parse_one_file(infilename, volnum, options, shortfilename)

errfile.close()
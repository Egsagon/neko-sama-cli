import os
import shutil
import tqdm
import string
import anchor
import nekosama
from nekosama.consts import root

from ffmpeg_progress_yield import FfmpegProgress as FP

FFMPEG = shutil.which('ffmpeg')

if not FFMPEG:
    anchor.BORDER_COLOR = anchor.COLOR.RED
    anchor.banner('Please install FFMPEG to your system before using this script.', title = 'Error')
    exit()

def main() -> None:

    client = nekosama.Client()

    anchor.FONT_COLOR = anchor.COLOR.BLUE

    anchor.banner('⛉ **NekoSama Downloader** ⛉\n\n$GREY(github.com/Egsagon)')

    query = anchor.entry('URL / NAME >')

    no_brackets = lambda s: s.replace('(', '[').replace(')', ']')
    allowed_chars = string.ascii_letters + string.digits + string.punctuation + ' éèàûâêî'
    thrust_chars = lambda s: ''.join(c for c in s if c in allowed_chars)

    if 'https://' in query:
        
        if '/episode/' in query:
            # Build manga URL from chapter URL
            
            slug = query.split('episode/')[1].split('/')[0]
            url = root + '/anime/info/' + slug
        
        else:
            url = query

    else:
        with anchor.awaiter('Searching for animes'):
            matches = client.search(query, 'VOSTFR')
        
        raw_lines = []
        for m in matches:
            raw = thrust_chars(no_brackets(m.title))
            
            if len(raw) > anchor.width() - 14:
                raw = raw[:anchor.width() - 11] + '...'
            
            raw_lines.append(f'$WHITE({raw})')
        
        index = anchor.select_large(raw_lines,
                                    title = 'Search results',
                                    justify_title = 'center',
                                    prompt = 'Select an item >',
                                    wrap_lines = False)
        
        slug = matches[index].name
        url = matches[index].url

    # Get anime tree
    try:
        anime = client.get_anime(url)

    except:
        anchor.banner('Error: Failed to fetch ressource.'
                      'The URL might be wrong or the server may be down.')
        exit()

    tree = list(anime.episodes)

    _min = 1
    _max = len(tree)

    def parse_range(string: str) -> list[int]:
        
        if string.isdecimal(): return [ int(string) ]
        
        start, stop = _min, _max
        if string:
            start, stop = tuple(map(int, string.split('-')))
        
        return [i for i in range(start, stop + 1)]

    def validate(string: str) -> bool:
        
        for index in parse_range(string):
            assert _min <= index <= _max
        
        return True

    pad = len(str(len(tree)))

    response = anchor.entry_large(
        [f'Episode **{str(i + 1).zfill(pad)}**: $WHITE(*{ep.title}*)' for i, ep in enumerate(tree)],
        f'Select a range ({_min}-{_max} included; default=all) >',
        validator = validate,
        title = 'Anime available episodes',
        justify_title = 'center',
        wrap_lines = False
    )

    indexes = parse_range(response)

    r = ' ; '.join(map(str, indexes))
    anchor.banner(f'**$BLUE(Ready to download chapters:)**\n{r}\n$GREY(Press <Enter> to confirm)')

    input(anchor._ansi(anchor.COLOR.GREY) + '<Press enter>' + anchor._ansi())

    print()
    directory = f'./{slug}/'
    os.makedirs(directory, exist_ok = True)

    for index in tqdm.tqdm(
        iterable = indexes,
        desc = 'Total progress',
        dynamic_ncols = True,
        bar_format = '{desc} {bar} {n_fmt}/{total_fmt}',
        total = len(indexes),
        ascii = '─═',
        colour = 'blue'
    ):
        episode = tree[index - 1]
        
        path = directory + str(index) + '.mp4'
        
        raw = episode.get_fragments()
        
        with open('temp.m3u', 'w') as file:
            file.write(raw)
        
        command = [
            FFMPEG,
            '-protocol_whitelist', 'file,http,https,tcp,tls,crypto',
            '-i', 'temp.m3u',
            '-acodec', 'copy',
            '-vcodec', 'copy',
            path, '-y'
        ]
        
        with tqdm.tqdm(
            iterable = FP(command).run_command_with_progress(),
            desc = f'Current [{str(index).zfill(4)}]',
            total = 100,
            dynamic_ncols = True,
            bar_format = '{desc} {bar} {n_fmt}/{total_fmt}',
            ascii = '─═',
            leave = False
        ) as bar:
            
            for progress in FP(command).run_command_with_progress():
                bar.update(int(progress) - bar.n)
        
        os.remove('temp.m3u')

    print()
    anchor.banner(f'Download successful!\n$GREY(Stuff was saved at *{directory}*)\nHave a nice day! ^^')

if __name__ == '__main__':
    
    try:
        main()
    
    except KeyboardInterrupt:
        exit()
    
    except Exception as err:
        print()
        
        anchor.BORDER_COLOR = anchor.COLOR.RED
        anchor.FONT_COLOR = anchor.COLOR.NORMAL
        
        cls = type(err).__name__
        anchor.banner(f'Unexpected {cls}: {err}', title = 'Error')
        
        print()
        raise err

# EOF


from busspider import extract_bus_info, json_encoder_default
from functional import seq
from pathlib import Path
import argparse
import arrow
import json



def path_to_bus_info(path):
    print('PATH:', path)
    bus_num, crawltime = path.stem.split('.')
    crawltime = arrow.get(crawltime, 'YYYY-MM-DD_HH-mm-ss')

    with path.open() as f:
        businfo = {'bus_num': bus_num,
                   'crawltime': crawltime,
                   **extract_bus_info(f.read())}
    return businfo


def save_to_file(res, outdir):
    outfile = outdir / res['bus_num'] / (res['crawltime'].format('YYYY-MM-DD') + '.json')
    outfile.parent.mkdir(parents=True, exist_ok=True)

    with outfile.open('a') as f:
        print(json.dumps(res, default=json_encoder_default), file=f)


def parseargs():
    parser = argparse.ArgumentParser(description='Extract bus info from HTML files.')
    parser.add_argument('INDIR', help='input folder')
    parser.add_argument('OUTDIR', help='output folder')
    return parser.parse_args()


if __name__ == '__main__':
    args = parseargs()
    input_dir, output_dir = Path(args.INDIR), Path(args.OUTDIR)
    output_dir
    print(input_dir, output_dir)
    # print(list(input_dir.glob('*/*.html')))
    
    seq(input_dir.glob('*/*.html'))\
        .map(path_to_bus_info)\
        .for_each(lambda res: save_to_file(res, output_dir))
    
    

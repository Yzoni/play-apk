import argparse
import os
import shutil
from pathlib import Path

from gpapi.googleplay import GooglePlayAPI
from gpapi.googleplay import RequestError

api = GooglePlayAPI(locale="en_US", timezone="UTC", device_codename="oneplus3")


def initial_login(email: str, password: str):
    api.login(email, password)
    print(f'gsfId: {api.gsfId}')
    print(f'authSubToken: {api.authSubToken}')


def download_apk(gsf_id: int, auth_sub_token: str, package_names: list, root: Path):
    api.login(None, None, gsf_id, auth_sub_token)

    for package_name in package_names:
        package_name = package_name.rstrip()
        try:
            print(f'Downloading {package_name}')
            version = api.details(package_name).get('details').get('appDetails').get('versionString')
            download = api.download(package_name)

            download_root = root / 'download'
            download_root.mkdir(exist_ok=True)
            download_location = download_root / f'{download.get("docId")}-{version}'
            download_location.mkdir(exist_ok=True)

            archive_location = root / 'bundled'
            archive_location.mkdir(exist_ok=True)

            filename = f'{download["docId"]}-{version}'
            print(f'    -> Version: {version}')
            for idx, a in enumerate(download['additionalData']):
                print(f'    Additional data: {idx}')
                print(f'        -> Type:    {a["type"]}')
                print(f'        -> Version: {a["versionCode"]}')
                print(f'        -> File:    {a["file"]}')
            for idx, a in enumerate(download['splits']):
                print(f'    Splits: {idx}')
                print(f'        -> Name:    {a["name"]}')
                print(f'        -> File:    {a["file"]}')
                with (download_location / f'{filename}-{a["name"]}.apk').open(mode='wb') as split:
                    for chunk in a.get('file').get('data'):
                        split.write(chunk)
                print('Download of base apk finished')
            with (download_location / f'{filename}-base.apk').open(mode='wb') as base:
                for chunk in download.get('file').get('data'):
                    base.write(chunk)
            print('Download of base apk finished')

            archive_file = f'{str(archive_location / filename)}'
            shutil.make_archive(archive_file, 'zip', str(download_location))
            print(f'Made archive at {archive_file}')

        except RequestError as e:
            print(f'Failed to download {package_name}')
            print(e)


def arg_login(args):
    initial_login(args.email, args.password)


def arg_download(args):
    if Path(args.package).exists() and Path(args.package).is_file():
        with open(args.package) as f:
            packages = [package for package in f]

    else:
        packages = [args.package]
    download_apk(args.gsfid, args.authsubtoken, packages, Path(args.out))


def main():
    parser = argparse.ArgumentParser(description='Google Play API CLI')
    subparsers = parser.add_subparsers(help='sub-command help')

    login = subparsers.add_parser('login', help='First time login')
    login.add_argument('--email', type=str, help='Google email', required=True)
    login.add_argument('--password', type=str, help='Google passwprd', required=True)
    login.set_defaults(func=arg_login)

    download = subparsers.add_parser('download', help='Download apk')
    if os.environ.get('GSFID') and os.environ.get('AUTHSUBTOKEN'):
        tokens_required = False
    else:
        tokens_required = True
    download.add_argument('--gsfid', type=int, help='gsfid', required=tokens_required,
                          default=os.environ.get('GSFID'))
    download.add_argument('--authsubtoken', type=str, help='authsubtoken', required=tokens_required,
                          default=os.environ.get('AUTHSUBTOKEN'))
    download.add_argument('--package', type=str, help='Package identifier or file containing list of packages',
                          required=True)
    download.add_argument('--out', type=str, help='Directory to download package to', default=Path(''))
    download.set_defaults(func=arg_download)

    args = parser.parse_args()
    if not args.__dict__:
        parser.print_help()
    else:
        args.func(args)

    Path(args.out).mkdir(exist_ok=True)


if __name__ == '__main__':
    main()

import click

from hew.ui import run


@click.command()
@click.argument('srcpath', type=click.Path(exists=True))
def cli(srcpath):

    ctx = {
        'srcpath': srcpath,
    }

    run(ctx)


if __name__ == '__main__':
    cli()

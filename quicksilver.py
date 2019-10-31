import click

@click.group()
def quicksilver():
    pass

@quicksilver.command()
def debug():
    '''for debug purpose'''
    click.echo('quicksilver debug')

@quicksilver.command()
def backtest():
    '''backtest'''
    click.echo('quicksilver backtest')

@quicksilver.command()
def run():
    '''run for production'''
    click.echo('quicksilver run')

if __name__ == '__main__':
    quicksilver()

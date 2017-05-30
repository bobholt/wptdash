from wptdash.factory import create_app

prod_app = create_app('production')

if __name__ == "__main__":
    prod_app.run()

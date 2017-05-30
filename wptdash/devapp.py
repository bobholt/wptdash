from wptdash.factory import create_app

dev_app = create_app('development')

if __name__ == "__main__":
    dev_app.run()

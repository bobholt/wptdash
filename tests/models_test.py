import wptdash.models as models
from tests._conf import app, db, session


class TestProduct(object):
    def test_product_model(self, session):
        product = models.Product(name='foo')

        session.add(product)
        session.commit()

        assert product.id > 0

from typing import List, Optional
from io import BytesIO
import matplotlib
from matplotlib import pyplot as plt
from dto import CategorySumOverPeriodDto

matplotlib.use('Agg')


class GraphService:
    def create_by_category_diagram(self, data: List[CategorySumOverPeriodDto], name: str) -> Optional[bytes]:
        if not data:
            return None
        labels = [by_category.category.name for by_category in data]
        data = [by_category.amount for by_category in data]

        fig = plt.figure()
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis('equal')
        ax.pie(data, labels=labels, autopct='%1.1f%%')
        ax.set_title(name)

        buf = BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        bts = buf.read()
        buf.close()
        return bts

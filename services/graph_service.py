from typing import Optional
from io import BytesIO
import matplotlib
from matplotlib import pyplot as plt
from entities import CategorySumOverPeriod, UserSumOverPeriodWithBalance

matplotlib.use("Agg")


class GraphService:
    def create_by_category_diagram(
        self, data: list[CategorySumOverPeriod], name: str
    ) -> Optional[bytes]:
        if not data:
            return None
        diagram_data: list[float] = []
        diagram_labels: list[str] = []
        for item in data:
            if item.amount > 0:
                diagram_data.append(item.amount)
                diagram_labels.append(item.category.name)
        return self._draw_figure(diagram_data, diagram_labels, name)

    def create_by_user_diagram(
        self, data: list[UserSumOverPeriodWithBalance], name: str
    ) -> Optional[bytes]:
        if not data:
            return None
        labels = [by_user.user.username or by_user.user.id for by_user in data]
        data = [by_user.amount for by_user in data]
        return self._draw_figure(data, labels, name)

    def _draw_figure(self, data: list[float], labels: list[str], name: str) -> bytes:
        fig = plt.figure()
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis("equal")
        ax.pie(data, labels=labels, autopct="%1.1f%%")
        ax.set_title(name)

        buf = BytesIO()
        fig.savefig(buf, format="png")
        buf.seek(0)
        bts = buf.read()
        buf.close()
        return bts

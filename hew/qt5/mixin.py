from PyQt5.QtCore import QEvent


class DraggingMixin:

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self._dragging_x = event.x()
        self._dragging_y = event.y()

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        x = event.globalX() - self._dragging_x
        y = event.globalY() - self._dragging_y
        self.move(x, y)


class ActivationHandoverMixin:

    def event(self, e):
        if e.type() == QEvent.WindowActivate:
            t = getattr(self, '_activation_target', None)
            if t is not None:
                t.activateWindow()
        return super().event(e)

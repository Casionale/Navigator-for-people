import npyscreen


# Форма со списком детей (checkbox-лист)
class FormChildrenList(npyscreen.ActionForm):
    def create(self):
        self.name = "Печать информации детей - выбор"

        self.options = [
            f"Ребёнок {i+1}" for i in range(100)  # можно сделать хоть 1000
        ]

        # MultiSelect позволяет выбрать несколько опций, с прокруткой
        self.selector = self.add(
            npyscreen.MultiSelect,
            values=self.options,
            scroll_exit=True,
            max_height=15,  # растягивается по форме
        )

        # Кнопка "Выбрать всё"
        self.select_all_btn = self.add(
            npyscreen.ButtonPress,
            name="Выбрать всё",
            when_pressed_function=self.select_all
        )

    def select_all(self):
        # Устанавливаем все индексы в выбранные
        self.selector.value = list(range(len(self.options)))
        self.display()  # обновить интерфейс

    def on_ok(self):
        # При нажатии ОК — показать выбранные элементы
        selected = self.selector.get_selected_objects()
        npyscreen.notify_confirm(
            "Вы выбрали:\n" + "\n".join(selected),
            title="Результат"
        )
        self.parentApp.setNextForm("MAIN")

    def on_cancel(self):
        # Возврат назад
        self.parentApp.setNextForm("MAIN")


class FilterChoiceForm(npyscreen.ActionForm):

    def create(self):
        self.name = "Использовать фильтр?"
        self.choice = self.add(npyscreen.TitleSelectOne,
                               name="Использовать фильтр?",
                               values=["Да", "Нет"],
                               max_height=4,
                               scroll_exit=True)

    def on_ok(self):
        if self.choice.value == [0]:  # Да
            self.parentApp.setNextForm("USER_SELECT")
        else:  # Нет
            self.parentApp.setNextForm("MAIN")

    def on_cancel(self):
        self.parentApp.setNextForm(None)

class UserSelectForm(npyscreen.ActionForm):
    def create(self):
        self.name = "Выбор пользователей"
        self.user_list = [f"Пользователь {i+1}" for i in range(20)]  # примерный список
        self.selector = self.add(npyscreen.MultiSelect,
                                 values=self.user_list,
                                 scroll_exit=True,
                                 max_height=12)

    def on_ok(self):
        selected = self.selector.get_selected_objects()
        npyscreen.notify_confirm("Выбраны:\n" + "\n".join(selected), title="Фильтр")
        # Сохраняем в переменную приложения
        self.parentApp.filtered_users = selected

        self.parentApp.setNextForm("MAIN")

    def on_cancel(self):
        self.parentApp.setNextForm("MAIN")

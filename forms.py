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
        self.parentApp.setNextForm("MAIN")


class FilterChoiceForm(npyscreen.ActionForm):

    def create(self):
        self.name = "Приветствие"
        self.add(npyscreen.FixedText, value='Добро пожаловать в Навигатор для людей', editable=False, color="STANDOUT")
        self.add(npyscreen.FixedText, value='Нажмите OK внизу справа если хотите использовать фильтр', editable=False)
        self.add(npyscreen.FixedText, value='Нажмите Cancel внизу справа если НЕ хотите использовать фильтр', editable=False)

    def on_ok(self):
        self.parentApp.application.use_filter = True
        self.parentApp.setNextForm("USER_SELECT")

    def on_cancel(self):
        self.parentApp.application.use_filter = False
        self.parentApp.setNextForm("MAIN")

class UserSelectForm(npyscreen.ActionForm):
    def create(self):
        self.name = "Выбор пользователей"

    def beforeEditing(self):
        self.parentApp.application.get_all_groups()
        self.user_list = [t for t in self.parentApp.application.get_teachers()]

        self.selector = self.add(npyscreen.MultiSelect,
                                 values=self.user_list,
                                 scroll_exit=True,
                                 max_height=12)

    def on_ok(self):
        selected = self.selector.get_selected_objects()
        self.parentApp.application.select_groups(selected)
        npyscreen.notify_confirm(f"Выбрано {len(self.parentApp.application.groups)} групп\n"
                                 "Выбраны:\n" + "\n".join(selected), title="Фильтр")
        # Сохраняем в переменную приложения
        self.parentApp.filtered_users = selected

        self.parentApp.setNextForm("MAIN")

    def on_cancel(self):
        self.parentApp.setNextForm("MAIN")

class GroupsSelectForm(npyscreen.ActionForm):
    def create(self):
        self.name = "Выбор групп"

    def beforeEditing(self):
        self.parentApp.application.get_all_groups()
        self.user_list = [
                            f'{i} {t["id"]} {t["program_name"]} {t["name"]}'
                            for i, t in enumerate(self.parentApp.application.groups)
                        ]

        self.selector = self.add(npyscreen.MultiSelect,
                                 values=self.user_list,
                                 scroll_exit=True,
                                 max_height=15)

    def on_ok(self):
        selected = self.selector.get_selected_objects()
        selected_groups_str = ''
        for s in selected:
            selected_groups_str += f"{s[:s.index(' ')]} "
        self.parentApp.application.selected_groups = selected_groups_str

        self.parentApp.setNextForm(self.parentApp.user_next_form)

    def on_cancel(self):
        self.parentApp.setNextForm("MAIN")

class PrintChildForm(npyscreen.ActionForm):
    info = None
    def create(self):
        self.name = "Печать информации о детях"
        self.info = self.add(npyscreen.MultiLine, values=[], max_height=10, scroll_exit=True, editable=False)

    def beforeEditing(self):
        msg = self.parentApp.application.printChildren()
        self.info.values = msg

    def on_ok(self):
        self.parentApp.user_next_form = "MAIN"
        self.parentApp.setNextForm("MAIN")

    def on_cancel(self):
        self.on_ok()


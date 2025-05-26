import npyscreen
from forms import FormChildrenList, FilterChoiceForm, UserSelectForm, GroupsSelectForm, PrintChildForm, \
    PrintStatOfAgesForm, PrintListFromOrderForm, CloseDaysForm
from application import App

class MainMenuForm(npyscreen.FormBaseNew):

    def create(self):
        self.name = "Навигатор для людей"
        self.add(npyscreen.FixedText, value="", editable=False, color="STANDOUT")

        self.hello_string = self.add(npyscreen.FixedText, value="Выберите действие:", editable=False, color="LABEL")

        # Каждая кнопка — это пункт меню, обрабатываем через соответствующий метод-заглушку
        self.add(npyscreen.ButtonPress, name="0. Печать информации детей", when_pressed_function=self.action_0)
        self.add(npyscreen.ButtonPress, name="3. Печать статистики по возрастам", when_pressed_function=self.action_3)
        self.add(npyscreen.ButtonPress, name="4. Печать списка из заявок", when_pressed_function=self.action_4)
        self.add(npyscreen.ButtonPress, name="5. Внести в навигатор свои грязные буквы",
                 when_pressed_function=self.action_5)
        self.add(npyscreen.ButtonPress, name="6. Найти проблемные группы", when_pressed_function=self.action_6)
        self.add(npyscreen.ButtonPress, name="7. Найти дубликаты детей", when_pressed_function=self.action_7)
        self.add(npyscreen.ButtonPress, name="8. По возрастам и уникальные", when_pressed_function=self.action_8)
        self.add(npyscreen.ButtonPress, name="9. Количество детей по программам", when_pressed_function=self.action_9)
        self.add(npyscreen.ButtonPress, name="10. Принудительная заявка детей в группу",
                 when_pressed_function=self.action_10)
        self.add(npyscreen.ButtonPress, name="11. Принудительное зачисление детей в мероприятие",
                 when_pressed_function=self.action_11)
        self.add(npyscreen.ButtonPress, name="12. Принять на обучение", when_pressed_function=self.action_12)
        self.add(npyscreen.ButtonPress, name="13. Генерировать выходную диагностику",
                 when_pressed_function=self.action_13)
        self.add(npyscreen.ButtonPress, name="14. Поиск детей онлайн по ФИО", when_pressed_function=self.action_14)
        self.add(npyscreen.ButtonPress, name="15. Генерировать входную диагностику",
                 when_pressed_function=self.action_15)
        self.add(npyscreen.ButtonPress, name="Выход", when_pressed_function=self.exit_app)

    def beforeEditing(self):
        # При входе на форму обновим список
        self.hello_string.value = f"Добро пожаловать, {self.parentApp.filtered_users[0]
        if len(self.parentApp.filtered_users) == 1 else 'божественный пользователь'}!"

    # Заглушки для обработки кнопок
    def _show_stub(self, action_name):
        npyscreen.notify_confirm(f"Выполняется действие: {action_name}", title="Заглушка")

    def action_0(self):
        self.parentApp.setNextForm("GROUPS_SELECT")
        self.parentApp.user_next_form = "PRINT_CHILD"
        self.editing = False

    def action_3(self):
        self.parentApp.setNextForm("PRINT_STATOFAGES")
        self.editing = False

    def action_4(self):
        self.parentApp.setNextForm("GROUPS_SELECT")
        self.parentApp.user_next_form = "PRINT_FROMORDER"
        self.editing = False

    def action_5(self):
        self.parentApp.setNextForm('CLOSE_DAY')
        self.editing = False

    def action_6(self): self._show_stub("Найти проблемные группы")

    def action_7(self): self._show_stub("Найти дубликаты детей")

    def action_8(self): self._show_stub("По возрастам и уникальные")

    def action_9(self): self._show_stub("Количество детей по программам")

    def action_10(self): self._show_stub("Принудительная заявка детей в группу")

    def action_11(self): self._show_stub("Принудительное зачисление детей в мероприятие")

    def action_12(self): self._show_stub("Принять на обучение")

    def action_13(self): self._show_stub("Генерировать выходную диагностику")

    def action_14(self): self._show_stub("Поиск детей онлайн по ФИО")

    def action_15(self): self._show_stub("Генерировать входную диагностику")

    def exit_app(self):
        self.parentApp.setNextForm(None)
        self.editing = False


class MyApp(npyscreen.NPSAppManaged):
    user_next_form = None
    def __init__(self):
        super().__init__()
        self.filtered_users = ['']
        self.application = App()

    def onStart(self):
        self.filtered_users = []
        self.addForm("FILTER_CHOICE", FilterChoiceForm)
        self.addForm("USER_SELECT", UserSelectForm)
        self.addForm("MAIN", MainMenuForm)
        self.addForm("CHILD_LIST", FormChildrenList)
        self.addForm("GROUPS_SELECT", GroupsSelectForm)
        self.addForm("PRINT_CHILD", PrintChildForm)
        self.addForm("PRINT_STATOFAGES", PrintStatOfAgesForm)
        self.addForm("PRINT_FROMORDER", PrintListFromOrderForm)
        self.addForm("CLOSE_DAY", CloseDaysForm)


        self.setNextForm("FILTER_CHOICE")
        is_auth = self.application.auth()
        if is_auth == 0:
            npyscreen.notify_confirm("Авторизация удалась", title="Авторизация")
            pass
        else:
            npyscreen.notify_confirm(f"Авторизация НЕ удалась: {is_auth}", title="Авторизация")
            self.setNextForm(None)


if __name__ == "__main__":
    app = MyApp()
    app.run()

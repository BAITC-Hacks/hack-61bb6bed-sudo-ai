import { test, expect, type Page } from "@playwright/test";
test.beforeEach(async ({page}) => {
  await page.route("**/api/v1/tasks/*/interview", route=>route.fulfill({json:{summary:"",questions:[],source:"local_fallback",warning:"Тест ручного заполнения"}}));
});
const password = "Sana-browser-test-2026";
async function register(page: Page, email: string, student = false) {
  await page.goto("/register");
  if (student) await page.getByRole("button", { name: "Я студент" }).click();
  await page
    .getByLabel("Ваше имя")
    .fill(student ? "Команда Тест" : "Бизнес Тест");
  await page.getByLabel("Email", { exact: true }).fill(email);
  await page.getByLabel("Пароль", { exact: true }).fill(password);
  await page
    .getByRole("button", { name: "Создать аккаунт", exact: true })
    .click();
  await expect(page).toHaveURL(/dashboard/);
}
test("real registration → challenge → proposal → selection", async ({
  browser,
}) => {
  const business = await browser.newContext();
  const student = await browser.newContext();
  const bp = await business.newPage();
  const sp = await student.newPage();
  const errors: string[] = [];
  for (const p of [bp, sp]) p.on("pageerror", (e) => errors.push(e.message));
  const unique = Date.now();
  await register(bp, `business-${unique}@example.com`);
  await bp.getByRole("link", { name: "Создать задачу", exact: true }).click();
  await bp
    .getByLabel("Расскажите о вашей потребности")
    .fill("Нужно автоматизировать обработку 500 заявок в день.");
  await bp.getByRole("button", { name: "Создать черновик" }).click();
  await expect(bp).toHaveURL(/\/tasks\/.+\/edit/);
  const id = bp.url().split("/tasks/")[1].split("/")[0];
  const title = `Классификация заявок ${unique}`;
  const fields: Record<string, string> = {
    "Название задачи *": title,
    "Проблема бизнеса *": "500 обращений ежедневно сортируются вручную.",
    "Цель проекта *": "Сократить время обработки с 4 часов до 1 часа.",
    "Ожидаемый результат *": "REST API, документация и отчёт с метриками.",
    "Критерии успеха *": "Точность 80% на 100 тестовых примерах.",
    "Срок и объём работы *": "3 недели на MVP и проверку метрик.",
  };
  const steps = ["Проблема бизнеса *", "Целевая аудитория", "Цель проекта *", "Ожидаемый результат *", "Критерии успеха *", "Ограничения", "Данные и ресурсы", "Срок и объём работы *", "Риски и безопасность", "Название задачи *"];
  for (const label of steps) {
    if(fields[label]) await bp.getByLabel(label, {exact:true}).fill(fields[label]);
    await bp.getByRole("button", {name:"Далее",exact:true}).click();
  }
  await bp.getByLabel("Python", { exact: true }).check();
  await bp.getByRole("button", {name:"К проверке",exact:true}).click();
  await bp.getByRole("button", { name: "Оценить задачу", exact: true }).click();
  await expect(bp.getByRole("status")).toContainText("Карточка обновлена");
  await bp.getByRole("button", { name: "Опубликовать", exact: true }).click();
  await expect(bp).toHaveURL(new RegExp(`/tasks/${id}$`));
  await register(sp, `student-${unique}@example.com`, true);
  await sp.getByRole("link", { name: "Мои команды", exact: true }).click();
  await sp.getByRole("button", { name: "Новая команда" }).click();
  await sp
    .getByLabel("Название команды", { exact: true })
    .fill(`Horizon ${unique}`);
  await sp
    .getByLabel("О команде", { exact: true })
    .fill("Разрабатываем прототипы на Python.");
  await sp.getByLabel("Python", { exact: true }).check();
  await sp
    .getByRole("button", { name: "Создать команду", exact: true })
    .click();
  await expect(sp).toHaveURL(/\/teams\/.+/);
  await sp.goto(`/tasks/${id}`);
  await sp
    .getByLabel("Почему ваша команда?")
    .fill("У нас есть опыт классификации обращений.");
  await sp
    .getByLabel("Как вы решите задачу?")
    .fill("Подготовим baseline и проверим качество на отложенных данных.");
  await sp.getByLabel("Предлагаемый срок", { exact: true }).fill("3 недели");
  await sp
    .getByRole("button", { name: "Подать предложение", exact: true })
    .click();
  await expect(sp.getByRole("status")).toContainText("Предложение отправлено");
  await bp.reload();
  await bp
    .getByRole("button", { name: "Выбрать команду", exact: true })
    .click();
  await bp.getByRole("button", { name: "Подтвердить выбор" }).click();
  await expect(
    bp.getByText("Команда выбрана", { exact: true }).first(),
  ).toBeVisible();
  await sp.goto("/proposals");
  await expect(sp.getByText("Выбрана", { exact: true })).toBeVisible();
  await bp.reload();
  await expect(
    bp.getByRole("link", { name: "Бизнес Тест Бизнес" }),
  ).toBeVisible();
  await bp.getByRole("button", { name: "Выйти", exact: true }).click();
  await expect(
    bp.getByRole("link", { name: "Войти", exact: true }),
  ).toBeVisible();
  await bp.goto("/login");
  await bp
    .getByLabel("Email", { exact: true })
    .fill(`business-${unique}@example.com`);
  await bp.getByLabel("Пароль", { exact: true }).fill(password);
  await bp.getByRole("button", { name: "Войти в аккаунт" }).click();
  await expect(bp).toHaveURL(/dashboard/);
  expect(errors).toEqual([]);
  await business.close();
  await student.close();
});
test("mobile catalog and navigation fit screen", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/catalog");
  await expect(
    page.getByRole("heading", { name: "Каталог задач" }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.getByRole("button", { name: "Открыть меню" }).click();
  await expect(page.getByRole("link", { name: "Каталог задач" })).toBeVisible();
  await page.getByRole("button", { name: "Закрыть меню" }).click();
  await page
    .getByRole("link", { name: "Создать аккаунт", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Создать аккаунт", exact: true }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
});

test("welcome role choice preserves selected role and fits mobile", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Большие дела начинаются с вас." })).toBeVisible();
  await page.getByRole("link", {name: /02 \/ СТУДЕНТЫ/}).click();
  await expect(page).toHaveURL(/login\?role=student/);
  await expect(page.getByLabel("Email", {exact:true})).toHaveValue("student.demo@example.com");
  await page.goto("/");
  await page.getByRole("link", {name: /01 \/ БИЗНЕС/}).click();
  await expect(page).toHaveURL(/login\?role=business/);
  await expect(page.getByLabel("Email", {exact:true})).toHaveValue("business.demo@example.com");
  await page.setViewportSize({width:390,height:844});
  await page.goto("/");
  await expect(page.getByRole("link", {name: /02 \/ СТУДЕНТЫ/})).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});

test("business dashboard creates a draft directly", async ({ page }) => {
  await page.setViewportSize({width:1440,height:1000});
  await register(page, `quick-${Date.now()}@example.com`);
  await page.screenshot({path:"../artifacts/business-liquid.png", fullPage:true});
  await page.getByLabel("В чём ваша задача?").fill("Нужно автоматизировать обработку 500 обращений клиентов в день.");
  await page.getByRole("button",{name:"Создать черновик",exact:true}).click();
  await expect(page).toHaveURL(/\/tasks\/.+\/edit/);
});

test("prefilled business demo logs into a real account", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", {name: /01 \/ БИЗНЕС/}).click();
  await expect(page.getByLabel("Пароль", {exact:true})).toHaveValue("Sana-Demo-Business-2026");
  await page.screenshot({path:"../artifacts/demo-login.png", fullPage:true});
  await page.getByRole("button", {name:"Войти в аккаунт",exact:true}).click();
  await expect(page).toHaveURL(/dashboard/);
  await expect(page.getByRole("link",{name:"Демо Бизнес Бизнес"})).toBeVisible();
});

test("task deck saves answers, navigates back, and has no XP panel", async ({page}) => {
  await register(page, `deck-${Date.now()}@example.com`);
  await expect(page.getByRole("region",{name:"Ваш прогресс"})).toHaveCount(0);
  await page.getByLabel("В чём ваша задача?").fill("Тестовая задача пошагового редактора для проверки сохранения.");
  await page.getByRole("button",{name:"Создать черновик",exact:true}).click();
  await page.getByRole("button",{name:"Продолжить без AI",exact:true}).click();
  await page.getByLabel("Проблема бизнеса *",{exact:true}).fill("Проверка колоды");
  await page.getByRole("button",{name:"Далее",exact:true}).click();
  await expect(page.getByRole("heading",{name:"Кто будет пользоваться решением?"})).toBeVisible();
  await page.getByRole("button",{name:"Назад",exact:true}).click();
  await expect(page.getByLabel("Проблема бизнеса *",{exact:true})).toHaveValue("Проверка колоды");
  await page.reload();
  await page.getByRole("button",{name:"Продолжить без AI",exact:true}).click();
  await expect(page.getByLabel("Проблема бизнеса *",{exact:true})).toHaveValue("Проверка колоды");
  await page.setViewportSize({width:390,height:844});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  for(let i=0;i<10;i++) await page.getByRole("button",{name:"Далее",exact:true}).click();
  await page.getByLabel("Python",{exact:true}).check();
  await page.getByRole("button",{name:"К проверке",exact:true}).click();
  await expect(page.getByRole("heading",{name:"Проверьте вашу задачу"})).toBeVisible();
  await page.getByRole("button",{name:/Навыки команды/}).click();
  await expect(page.getByLabel("Python",{exact:true})).toBeChecked();
  await page.getByRole("button",{name:"Сохранить и выйти"}).click();
  await expect(page).toHaveURL(/dashboard/);
});


test("prefilled student demo logs into a student account", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", {name: /02 \/ СТУДЕНТЫ/}).click();
  await expect(page.getByLabel("Email", {exact:true})).toHaveValue("student.demo@example.com");
  await expect(page.getByLabel("Пароль", {exact:true})).toHaveValue("Sana-Demo-Student-2026");
  await page.getByRole("button", {name:"Войти в аккаунт",exact:true}).click();
  await expect(page).toHaveURL(/dashboard/);
  const user = await page.request.get("/api/v1/auth/me");
  expect(user.ok()).toBe(true);
  expect((await user.json()).role).toBe("student");
  await page.reload();
  await expect(page).toHaveURL(/dashboard/);
});

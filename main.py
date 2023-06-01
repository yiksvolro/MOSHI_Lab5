import random
import copy
from prettytable import PrettyTable
from colorama import Fore, Style


max_fitness = 2000
population_size = 50
max_generations = 50
mutation_rate = 0.1
crossover_rate = 0.9


class Cls:
    def __init__(self, name, cls_teacher):
        self.name = name
        self.cls_teacher = cls_teacher


class Teacher:
    def __init__(self, name, lessons):
        self.name = name
        self.lessons = lessons


class Lesson:
    def __init__(self, cls="None", teacher=None, name="None", special_room_required=False,
                 day_number=0, lesson_number=0, room=""):
        self.cls = cls
        self.teacher = teacher
        self.name = name
        self.special_room_required = special_room_required
        self.day_number = day_number
        self.lesson_number = lesson_number
        self.room = room


# Генерація випадкового розкладу
def generate_schedule(lesson_names, teachers, classes, num_lessons, num_classes, num_days,
                      max_lessons_per_day, room_names):
    schedule = []
    for i in range(num_classes):
        schedule.append([])
        for j in range(num_days):
            schedule[i].append([])
    for i in range(num_classes):
        for j in range(num_lessons):
            random_lesson = random.choice(lesson_names)
            if random_lesson[0] in classes[i].cls_teacher.lessons:
                random_teacher = classes[i].cls_teacher
            else:
                while True:
                    random_teacher = random.choice(teachers)
                    if random_lesson[0] in random_teacher.lessons:
                        break
            if random_lesson[1]:
                random_room = random_lesson[2]
            else:
                random_room = random.choice(room_names[:num_classes])
            day_number = j % max_lessons_per_day
            lesson_number = len(schedule[i][day_number])
            schedule[i][day_number].append(Lesson(classes[i], random_teacher, random_lesson[0],
                                                  random_lesson[1], day_number + 1, lesson_number + 1, random_room))
    for i in range(num_classes):
        for j in range(num_days * max_lessons_per_day - num_lessons):
            day_number = j % max_lessons_per_day
            schedule[i][day_number].append(None)

    return schedule


def fitness(schedule, num_lessons, max_lessons_per_day):
    fitness_score = max_fitness

    for class_schedule in schedule:

        # Перевірка кількості уроків на день
        for day in class_schedule:
            num_lessons_per_day = len(day)
            if num_lessons_per_day > max_lessons_per_day:
                fitness_score -= 10 * (num_lessons_per_day - max_lessons_per_day)

        # Перевірка вчитель відповідає предмету
        for day in class_schedule:
            for lesson in day:
                if lesson is not None:
                    if lesson.name not in lesson.teacher.lessons:
                        fitness_score -= 10

        # Перевірка класний керівник веде хоча б половину предметів
        class_teacher_lessons = 0
        for day in class_schedule:
            for lesson in day:
                if lesson is not None:
                    if lesson.cls.cls_teacher.name == lesson.teacher.name:
                        class_teacher_lessons += 1
        if class_teacher_lessons < (num_lessons / 2):
            fitness_score -= 50

        # Перевірка вікно у розкладі
        window_errors = 0
        for day in class_schedule:
            lesson_amount = len(day)
            for lesson_index in range(lesson_amount):
                if day[lesson_index] is None:
                    for rest_index in range(lesson_index + 1, lesson_amount):
                        if day[rest_index] is not None:
                            window_errors += 1
        fitness_score -= 10 * window_errors

    # Перевірка вчитель веде 2 уроки одночасно та однакові кімнати зайняті одночасно
    same_teacher_errors = 0
    same_room_errors = 0
    all_lessons = []
    for class_schedule in schedule:
        for day in class_schedule:
            for lesson in day:
                all_lessons.append(lesson)
    for lesson_index in range(len(all_lessons)):
        for another_lesson_index in range(lesson_index + 1, len(all_lessons)):
            first_lesson = all_lessons[lesson_index]
            second_lesson = all_lessons[another_lesson_index]
            if first_lesson is not None and second_lesson is not None:
                if (first_lesson.day_number == second_lesson.day_number) and \
                        (first_lesson.lesson_number == second_lesson.lesson_number) and \
                        (first_lesson.teacher.name == second_lesson.teacher.name):
                    same_teacher_errors += 1
                if (first_lesson.day_number == second_lesson.day_number) and \
                        (first_lesson.lesson_number == second_lesson.lesson_number) and \
                        (first_lesson.room == second_lesson.room):
                    same_room_errors += 1
    fitness_score -= 10 * same_teacher_errors
    fitness_score -= 10 * same_room_errors

    return fitness_score


def mutate(schedule, lesson_names, teachers, room_names, num_classes):
    if random.random() < mutation_rate:
        for class_schedule in schedule:
            for day in class_schedule:
                for lesson in day:
                    if lesson is not None:
                        if random.random() < mutation_rate and lesson is not None:
                            random_lesson = random.choice(lesson_names)
                            lesson.name = random_lesson[0]
                            lesson.special_room_required = random_lesson[1]
                            if random_lesson[1]:
                                lesson.room = random_lesson[2]
                            else:
                                lesson.room = random.choice(room_names[:num_classes])
                            if random_lesson[0] in lesson.cls.cls_teacher.lessons:
                                random_teacher = lesson.cls.cls_teacher
                            else:
                                while True:
                                    random_teacher = random.choice(teachers)
                                    if random_lesson[0] in random_teacher.lessons:
                                        break
                            lesson.teacher = random_teacher

def crossover(parent1_schedule, parent2_schedule, num_lessons, num_classes, num_days, max_lessons_per_day):
    child_schedule = []
    for i in range(num_lessons):
        child_schedule.append([])
        for j in range(num_days):
            child_schedule[i].append([])
    for i in range(num_classes):
        for j in range(num_days):
            crossover_class_point = random.randint(0, max_lessons_per_day - 1)
            child_schedule[i][j] = \
                parent1_schedule[i][j][:crossover_class_point] + parent2_schedule[i][j][crossover_class_point:]

    return child_schedule


def genetic_algorithm(lesson_names, teachers, classes, num_lessons, num_classes,
                      num_days, max_lessons_per_day, room_names):
    population = [generate_schedule(lesson_names, teachers, classes, num_lessons, num_classes,
                                    num_days, max_lessons_per_day, room_names) for _ in range(population_size)]
    best_schedule = copy.deepcopy(max(population, key=lambda x: fitness(x, num_lessons, max_lessons_per_day)))
    best_fitness = fitness(best_schedule, num_lessons, max_lessons_per_day)

    for generation in range(max_generations):
        fitness_scores = [fitness(schedule, num_lessons, max_lessons_per_day) ** 5 for schedule in population]
        selected_schedules = []

        for one_population in population:

            current_fitness = fitness(one_population, num_lessons, max_lessons_per_day)
            if current_fitness == max_fitness:
                return copy.deepcopy(one_population)
            elif fitness(one_population, num_lessons, max_lessons_per_day) > best_fitness:
                best_schedule = copy.deepcopy(one_population)
                best_fitness = fitness(best_schedule, num_lessons, max_lessons_per_day)

            # Турнірна вибірка
            new_children = random.choices(population, weights=fitness_scores, k=10)
            child = copy.deepcopy(max(new_children, key=lambda x: fitness(x, num_lessons, max_lessons_per_day)))

            mutate(child, lesson_names, teachers, room_names, num_classes)
            selected_schedules.append(child)

        population = selected_schedules

    result_schedules = max(population, key=lambda x: fitness(x, num_lessons, max_lessons_per_day))
    if fitness(result_schedules, num_lessons, max_lessons_per_day) > best_fitness:
        best_schedule = result_schedules
    return best_schedule


def print_schedule(schedule, num_days, max_lessons_per_day, num_classes, class_names):
    table = PrettyTable()
    line_color = Fore.GREEN
    table.field_names = [line_color + "Day", "Lesson Number"] + class_names[:num_classes]

    for day_index in range(num_days):
        for lesson_index in range(max_lessons_per_day):
            lessons = []
            for class_index in range(num_classes):
                if lesson_index >= len(schedule[0][day_index]):
                    lessons.append(Lesson(" ", Teacher(" ", []), " "))
                else:
                    lessons.append(schedule[class_index][day_index][lesson_index])

            table.add_row(
                [f"Day {day_index + 1}" if lesson_index == 0 else " ", f"Lesson {lesson_index + 1}"] +
                [f"{lesson.name}\n{lesson.teacher.name}\n{lesson.room}" for lesson in lessons])

            if lesson_index < max_lessons_per_day - 1:
                line = [line_color + "─" * 8, line_color + "─" * 12] + [line_color + "─" * 15] * num_classes
                table.add_row(line)

        if day_index < num_days - 1:
            line = [line_color + "━" * 8, line_color + "━" * 12] + [line_color + "━" * 15] * num_classes
            table.add_row(line)
            table.add_row([""] * (num_classes + 2))

    # Замінити вертикальні лінії на суцільні
    table.horizontal_char = line_color + "━"
    table.junction_char = line_color + "┿"
    table.vertical_char = line_color + "┃"

    print(Style.BRIGHT + str(table))
    print(Style.RESET_ALL)





def write_data_to_file(filename, num_lessons, num_classes, num_days, max_lessons_per_day,
                       teachers, room_names, class_names, lesson_names):
    with open(filename, 'w') as file:
        file.write(f"{num_lessons}\n")
        file.write(f"{num_classes}\n")
        file.write(f"{num_days}\n")
        file.write(f"{max_lessons_per_day}\n")

        for teacher in teachers:
            lessons_str = ", ".join(teacher.lessons)
            file.write(f"{teacher.name}: {lessons_str}\n")

        for room_name in room_names:
            file.write(f"{room_name}\n")

        for class_name in class_names:
            file.write(f"{class_name}\n")

        for lesson_name in lesson_names:
            requires_room = str(lesson_name[1]).lower()
            room_name = lesson_name[2]
            file.write(f"{lesson_name[0]}, {requires_room}, {room_name}\n")



def read_data_from_file(filename):
    with open(filename, 'r') as file:
        lines = file.readlines()

    num_lessons = int(lines[0].strip())
    num_classes = int(lines[1].strip())
    num_days = int(lines[2].strip())
    max_lessons_per_day = int(lines[3].strip())

    teachers = []
    for line in lines[4:8]:
        name, lessons_str = line.split(":")
        lessons = [lesson.strip() for lesson in lessons_str.split(",")]
        teachers.append(Teacher(name.strip(), lessons))

    room_names = [name.strip() for name in lines[8:14]]
    class_names = [name.strip() for name in lines[14:14 + num_classes]]

    lesson_names = []
    for line in lines[14 + num_classes:14 + num_classes + num_lessons]:
        values = line.split(",")
        if len(values) == 3:
            name, requires_room_str, room_name = values
            requires_room = requires_room_str.strip().lower() == "true"
            room_name = room_name.strip() if requires_room else "None"
            lesson_names.append([name.strip(), requires_room, room_name])

    return num_lessons, num_classes, num_days, max_lessons_per_day, teachers, room_names, class_names, lesson_names



def main():
    num_lessons = 23
    num_classes = 2
    num_days = 5
    max_lessons_per_day = 5

    teachers = [
        Teacher("Teacher 1", ["Math", "English", "Science", "History"]),
        Teacher("Teacher 2", ["Math", "English", "Science", "Music"]),
        Teacher("Teacher 3", ["Math", "English", "Science", "History"]),
        Teacher("Teacher 4", ["PE", "Choreography"]),
    ]

    room_names = ["СlassRoom 1", "ClassRoom 2", "ClassRoom 3", "PE Room", "Dance Room", "Music Room"]

    class_names = ["Class A", "Class B", "Class C"]

    lesson_names = [["Math", False, "None"], ["English", False, "None"], ["Science", False, "None"],
                    ["History", False, "None"], ["PE", True, "PE Room"], ["Choreography", True, "Dance Room"],
                    ["Music", True, "Music Room"]]

    input_file="input_file"
    output_file="output_file"
    # Запис даних у файл
    write_data_to_file(input_file, num_lessons, num_classes, num_days, max_lessons_per_day,
                       teachers, room_names, class_names, lesson_names)

    # Читання даних з файлу
    num_lessons, num_classes, num_days, max_lessons_per_day, teachers, room_names, class_names, lesson_names = read_data_from_file(input_file)

    classes = []
    for i in range(num_classes):
        classes.append(Cls(class_names[i], teachers[i]))

    best_schedule = genetic_algorithm(lesson_names, teachers, classes, num_lessons, num_classes,
                                      num_days, max_lessons_per_day, room_names)


    print_schedule(best_schedule, num_days, max_lessons_per_day, num_classes, class_names)
    print(f"Даний розклад має пристосованість {fitness(best_schedule, num_lessons, max_lessons_per_day)} із {max_fitness} можливих")


if __name__ == "__main__":
    main()
from django.test import TestCase
from .models import *
from faker import Faker
import random
from datetime import time

fake = Faker()

# Mover real_books al nivel del módulo
real_books = [
    ("J.K. Rowling", "Harry Potter and the Philosopher's Stone"),
    ("J.K. Rowling", "Harry Potter and the Chamber of Secrets"),
    ("J.K. Rowling", "Harry Potter and the Prisoner of Azkaban"),
    ("George Orwell", "1984"),
    ("George Orwell", "Animal Farm"),
    ("George Orwell", "Homage to Catalonia"),
    ("Leo Tolstoy", "War and Peace"),
    ("Leo Tolstoy", "Anna Karenina"),
    ("Jane Austen", "Pride and Prejudice"),
    ("Jane Austen", "Sense and Sensibility"),
    ("Jane Austen", "Emma"),
    ("Mark Twain", "The Adventures of Tom Sawyer"),
    ("Mark Twain", "Adventures of Huckleberry Finn"),
    ("Mark Twain", "The Prince and the Pauper"),
    ("Agatha Christie", "Murder on the Orient Express"),
    ("Agatha Christie", "The Murder of Roger Ackroyd"),
    ("Agatha Christie", "And Then There Were None"),
    ("Ernest Hemingway", "The Old Man and the Sea"),
    ("Ernest Hemingway", "A Farewell to Arms"),
    ("Ernest Hemingway", "For Whom the Bell Tolls"),
    ("F. Scott Fitzgerald", "The Great Gatsby"),
    ("F. Scott Fitzgerald", "Tender Is the Night"),
    ("F. Scott Fitzgerald", "This Side of Paradise"),
    ("Charles Dickens", "Great Expectations"),
    ("Charles Dickens", "Oliver Twist"),
    ("Charles Dickens", "David Copperfield"),
    ("Virginia Woolf", "To the Lighthouse"),
    ("Virginia Woolf", "Mrs. Dalloway"),
    ("Virginia Woolf", "Orlando"),
    ("Gabriel García Márquez", "Cien años de soledad"),
    ("Gabriel García Márquez", "El amor en los tiempos del cólera"),
    ("Gabriel García Márquez", "Crónica de una muerte anunciada"),
    ("Gabriel García Márquez", "El otoño del patriarca"),
    ("Gabriel García Márquez", "Del amor y otros demonios"),
    ("Gabriel García Márquez", "El general en su laberinto"),
    ("Gabriel García Márquez", "Memoria de mis putas tristes"),
    ("Harper Lee", "To Kill a Mockingbird"),
    ("J.R.R. Tolkien", "The Hobbit"),
    ("J.R.R. Tolkien", "The Lord of the Rings"),
    ("J.R.R. Tolkien", "The Silmarillion"),
    ("C.S. Lewis", "The Chronicles of Narnia"),
    ("C.S. Lewis", "The Screwtape Letters"),
    ("C.S. Lewis", "Mere Christianity"),
    ("Isabel Allende", "La casa de los espíritus"),
    ("Isabel Allende", "De amor y de sombra"),
    ("Isabel Allende", "Eva Luna"),
    ("Miguel de Cervantes", "Don Quijote de la Mancha"),
    ("Homer", "The Iliad"),
    ("Homer", "The Odyssey"),
    ("Dante Alighieri", "The Divine Comedy"),
    ("Victor Hugo", "Les Misérables"),
    ("Victor Hugo", "The Hunchback of Notre-Dame"),
    ("Fyodor Dostoevsky", "Crime and Punishment"),
    ("Fyodor Dostoevsky", "The Brothers Karamazov"),
    ("Fyodor Dostoevsky", "Notes from Underground"),
    ("Franz Kafka", "The Metamorphosis"),
    ("Franz Kafka", "The Trial"),
    ("Franz Kafka", "The Castle"),
    ("J.D. Salinger", "The Catcher in the Rye"),
    ("Herman Melville", "Moby-Dick"),
    ("Herman Melville", "Bartleby, the Scrivener"),
    ("Herman Melville", "Billy Budd"),
    ("Emily Brontë", "Wuthering Heights"),
    ("Charlotte Brontë", "Jane Eyre"),
    ("Anne Brontë", "The Tenant of Wildfell Hall"),
    ("Mary Shelley", "Frankenstein"),
    ("Bram Stoker", "Dracula"),
    ("Oscar Wilde", "The Picture of Dorian Gray"),
    ("Oscar Wilde", "The Importance of Being Earnest"),
    ("Oscar Wilde", "De Profundis"),
    ("Edgar Allan Poe", "The Raven"),
    ("Edgar Allan Poe", "The Tell-Tale Heart"),
    ("Edgar Allan Poe", "The Fall of the House of Usher"),
    ("Jules Verne", "Twenty Thousand Leagues Under the Sea"),
    ("Jules Verne", "Around the World in Eighty Days"),
    ("Jules Verne", "Journey to the Center of the Earth"),
    ("H.G. Wells", "The War of the Worlds"),
    ("H.G. Wells", "The Time Machine"),
    ("H.G. Wells", "The Invisible Man"),
    ("George R.R. Martin", "A Game of Thrones"),
    ("George R.R. Martin", "A Clash of Kings"),
    ("George R.R. Martin", "A Storm of Swords"),
    ("George R.R. Martin", "A Feast for Crows"),
    ("George R.R. Martin", "A Dance with Dragons"),
    ("Suzanne Collins", "The Hunger Games"),
    ("Suzanne Collins", "Catching Fire"),
    ("Suzanne Collins", "Mockingjay"),
    ("Stephen King", "The Shining"),
    ("Stephen King", "It"),
    ("Stephen King", "The Stand"),
    ("Stephen King", "Misery"),
    ("Stephen King", "Carrie"),
    ("Margaret Atwood", "The Handmaid's Tale"),
    ("Margaret Atwood", "Oryx and Crake"),
    ("Margaret Atwood", "The Testaments"),
    ("Khaled Hosseini", "The Kite Runner"),
    ("Khaled Hosseini", "A Thousand Splendid Suns"),
    ("Khaled Hosseini", "And the Mountains Echoed"),
]

def seed_data():
    # Eliminar datos existentes
    Exemplar.objects.all().delete()
    Llibre.objects.all().delete()
    Revista.objects.all().delete()
    CD.objects.all().delete()
    DVD.objects.all().delete()
    BR.objects.all().delete()
    Dispositiu.objects.all().delete()
    Pais.objects.all().delete()
    Llengua.objects.all().delete()
    Categoria.objects.all().delete()
    Prestec.objects.all().delete()
    Reserva.objects.all().delete()

    # Eliminar usuarios excepto superusuarios
    Usuari.objects.exclude(is_superuser=True).delete()

    # Definir categorías
    categories = [Categoria.objects.create(nom=fake.word()) for _ in range(5)]

    # Definir países y lenguas reales
    paisos = [Pais.objects.create(nom=country) for country in ["España", "Estados Unidos", "Reino Unido", "Francia", "Italia"]]
    llengües = [Llengua.objects.create(nom=language) for language in ["Español", "Inglés", "Francés", "Alemán", "Italiano"]]

    # Crear usuarios
    usuaris = []
    for _ in range(10):  # 10 usuarios
        usuari = Usuari.objects.create_user(
            username=fake.user_name(),
            password='qwerty12345',
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            email=fake.email(),
        )
        usuaris.append(usuari)

    # Crear libros únicos
    llibres = []
    for author, book in real_books:
        llibre = Llibre.objects.create(
            titol=book,
            autor=author,
            editorial=random.choice(["Penguin", "HarperCollins", "Macmillan"]),
            lloc=fake.city(),
            pais=random.choice(paisos),
            llengua=random.choice(llengües),
            data_edicio=fake.date_this_century(),
        )
        llibre.tags.set(random.sample(categories, k=random.randint(1, 3)))
        llibres.append(llibre)

    # Crear otros tipos de catálogo
    for _ in range(10):  # 10 revistas
        Revista.objects.create(
            titol=fake.sentence(),
            ISSN=fake.isbn13(),
            editorial=random.choice(["Nature", "Science", "IEEE"]),
            lloc=fake.city(),
            pais=random.choice(paisos),
            llengua=random.choice(llengües),
        )

    # Crear CDs con el campo 'duracio'
    for _ in range(10):  # 10 CDs
        duracion_minutos = random.randint(30, 120)  # Duración aleatoria entre 30 y 120 minutos
        duracion_horas = duracion_minutos // 60
        duracion_restantes = duracion_minutos % 60
        CD.objects.create(
            titol=fake.sentence(),
            autor=fake.name(),
            data_edicio=fake.date_this_century(),
            discografica=fake.company(),
            estil=fake.word(),
            duracio=time(hour=duracion_horas, minute=duracion_restantes),  # Convertir a formato hh:mm:ss
        )

    # Crear DVDs con el campo 'duracio'
    for _ in range(10):  # 10 DVDs
        duracion_minutos = random.randint(60, 180)  # Duración aleatoria entre 60 y 180 minutos
        duracion_horas = duracion_minutos // 60
        duracion_restantes = duracion_minutos % 60
        DVD.objects.create(
            titol=fake.sentence(),
            autor=fake.name(),
            data_edicio=fake.date_this_century(),
            duracio=time(hour=duracion_horas, minute=duracion_restantes),  # Convertir a formato hh:mm:ss
        )

    # Crear BluRays con el campo 'duracio'
    for _ in range(10):  # 10 BluRays
        duracion_minutos = random.randint(60, 180)  # Duración aleatoria entre 60 y 180 minutos
        duracion_horas = duracion_minutos // 60
        duracion_restantes = duracion_minutos % 60
        BR.objects.create(
            titol=fake.sentence(),
            autor=fake.name(),
            data_edicio=fake.date_this_century(),
            productora=fake.company(),
            duracio=time(hour=duracion_horas, minute=duracion_restantes),  # Convertir a formato hh:mm:ss
        )

    for _ in range(10):  # 10 dispositivos
        Dispositiu.objects.create(
            titol=fake.sentence(),
            autor=fake.name(),
            data_edicio=fake.date_this_century(),
        )

    # Crear ejemplares, préstamos y reservas
    for llibre in llibres:
        for _ in range(random.randint(1, 3)):  # 1 a 3 ejemplares por libro
            exemplar = Exemplar.objects.create(cataleg=llibre, registre=fake.uuid4(), exclos_prestec=False)
            usuari = random.choice(usuaris)

            # 50% de probabilidad de crear préstamo o reserva
            if random.choice([True, False]):
                Prestec.objects.create(usuari=usuari, exemplar=exemplar)
            else:
                Reserva.objects.create(usuari=usuari, exemplar=exemplar)

# Clase de prueba
class MyTestCase(TestCase):
    def setUp(self):
        seed_data()

    def test_example(self):
        self.assertEqual(Llibre.objects.count(), len(set([book[1] for book in real_books])))

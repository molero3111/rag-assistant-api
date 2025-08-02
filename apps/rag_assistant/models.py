from django.db import models
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from typing import List

load_dotenv()

class Animal(BaseModel):
    name: str = Field("The name of the animal.")
    species: str = Field("The species of the animal.")
    age: int = Field("The age of the animal in years.")
    habitat: str = Field("The natural habitat of the animal.")

class AnimalList(BaseModel):
    animals: List[Animal]
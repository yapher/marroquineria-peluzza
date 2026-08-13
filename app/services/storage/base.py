# app/services/storage/base.py
"""
Interfaz abstracta para backends de almacenamiento.
Cualquier backend nuevo debe implementar estos dos métodos.
"""
from abc import ABC, abstractmethod


class StorageBackend(ABC):
    """Contrato que deben cumplir todos los backends de storage."""

    @abstractmethod
    def upload(self, file) -> str | None:
        """
        Sube un archivo y devuelve su URL pública.
        Devuelve None si falla.

        Args:
            file: Objeto FileStorage de Werkzeug (request.files['campo'])

        Returns:
            str: URL pública de la imagen, o None si falló.
        """
        raise NotImplementedError

    @abstractmethod
    def delete(self, image_url: str) -> None:
        """
        Elimina una imagen del storage.
        No debe lanzar excepciones (best effort).

        Args:
            image_url: URL de la imagen a eliminar.
        """
        raise NotImplementedError
import unittest
import sys, os
import json
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../"))

from game.interface import Interface

class Test_Interface(unittest.TestCase):

    class Point(Interface):
        x: int
        y: int

    class Circle(Point):
        r: int
    
    class Entity(Interface):
        name: str

    class Player(Point, Entity):
        pass
    

    def test_returns_none(self):
        self.assertEqual(self.Point().x, None)
    
    def test_set_value(self):
        p = self.Point()
        p.x = 10
        self.assertEqual(p.x, 10)
    
    def test_inheritance(self):
        c = self.Circle()
        self.assertIsNone(c.x)
        self.assertIsNone(c.y)
        self.assertIsNone(c.r)


    def test_multiple_inheritance(self):
        p = self.Player()
        self.assertIsNone(p.x)
        self.assertIsNone(p.y)
        self.assertIsNone(p.name)
        

    def test_dumps(self):
        obj = { "x": 10, "y": 10 }
        p = self.Point(obj) # cast to Point object
        self.assertEqual(json.dumps(p), json.dumps(obj))

    
    def test_exception(self):
        p = self.Point()
        with self.assertRaises(AssertionError):
            p.x = self.Point


if __name__ == "__main__":
    unittest.main()
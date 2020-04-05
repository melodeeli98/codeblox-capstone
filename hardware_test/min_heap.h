#pragma once

#include <ArduinoSTL.h>

// Data structure for Min Heap
template <typename K, typename V>
class MinHeap
{
private:
  // vector to store heap elements
  std::vector<std::pair<K, V> *> A;

  // return parent of A[i]
  // don't call this function if i is already a root node
  int PARENT(int i);

  // return left child of A[i]
  int LEFT(int i);

  // return right child of A[i]
  int RIGHT(int i);

  // Recursive Heapify-down algorithm
  // the node at index i and its two direct children
  // violates the heap property
  void heapify_down(int i);

  // Recursive Heapify-up algorithm
  void heapify_up(int i);

public:
  // return size of the heap
  unsigned int size();

  // function to check if heap is empty or not
  bool empty();

  // insert key into the heap
  void push(K key, V value);

  // function to remove element with lowest priority (present at root)
  V pop();

  K topKey();

  // function to return element with lowest priority (present at root)
  V top();
};

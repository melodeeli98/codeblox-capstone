
#include "min_heap.h"
#include <ArduinoSTL.h>
using namespace std;

template <typename K, typename V>
int MinHeap<K, V>::PARENT(int i)
{
  return (i - 1) / 2;
}

// return left child of A[i]
template <typename K, typename V>
int MinHeap<K, V>::LEFT(int i)
{
  return (2 * i + 1);
}

// return right child of A[i]
template <typename K, typename V>
int MinHeap<K, V>::RIGHT(int i)
{
  return (2 * i + 2);
}

// Recursive Heapify-down algorithm
// the node at index i and its two direct children
// violates the heap property
template <typename K, typename V>
void MinHeap<K, V>::heapify_down(int i)
{
  // get left and right child of node at index i
  int left = LEFT(i);
  int right = RIGHT(i);

  int smallest = i;

  // compare A[i] with its left and right child
  // and find smallest value
  if (left < size() && *A[left] < *A[i])
    smallest = left;

  if (right < size() && *A[right] < *A[smallest])
    smallest = right;

  // swap with child having lesser value and
  // call heapify-down on the child
  if (smallest != i)
  {
    swap(A[i], A[smallest]);
    heapify_down(smallest);
  }
}

// Recursive Heapify-up algorithm
template <typename K, typename V>
void MinHeap<K, V>::heapify_up(int i)
{
  // check if node at index i and its parent violates
  // the heap property
  if (i && *A[PARENT(i)] > *A[i])
  {
    // swap the two if heap property is violated
    swap(A[i], A[PARENT(i)]);

    // call Heapify-up on the parent
    heapify_up(PARENT(i));
  }
}

template <typename K, typename V>
unsigned int MinHeap<K, V>::size()
{
  return A.size();
}

// function to check if heap is empty or not
template <typename K, typename V>
bool MinHeap<K, V>::empty()
{
  return size() == 0;
}

// insert key into the heap
template <typename K, typename V>
void MinHeap<K, V>::push(K key, V value)
{
  // insert the new element to the end of the vector
  A.push_back(new pair<K, V>(key, value));

  // get element index and call heapify-up procedure
  int index = size() - 1;
  heapify_up(index);
}

// function to remove element with lowest priority (present at root)
template <typename K, typename V>
V MinHeap<K, V>::pop()
{
  // replace the root of the heap with the last element
  // of the vector

  V value = A.at(0)->second;
  delete A[0];
  A[0] = A.back();
  A.pop_back();

  // call heapify-down on root node
  heapify_down(0);
  return value;
}

// function to return element with lowest priority (present at root)
template <typename K, typename V>
K MinHeap<K, V>::topKey()
{
  // else return the top (first) element
  return A.at(0)->first;
}

// function to return element with lowest priority (present at root)
template <typename K, typename V>
V MinHeap<K, V>::top()
{
  // else return the top (first) element
  return A.at(0)->second;
}

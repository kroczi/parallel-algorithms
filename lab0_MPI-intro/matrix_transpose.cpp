#include <iostream>
#include <cmath>
#include <mpi.h>
using namespace std;

const int ROWS = 14;
const int COLS = 8;

template <typename T>
T** matrix_create(int rows, int cols)
{
   T** array = new T* [rows];
   T* pool = new T[rows * cols];
   for(int i = 0; i < rows; i++, pool += cols)
       array[i] = pool;
   return array;
}

template <typename T>
void matrix_delete(T** array)
{
   delete [] array[0];
   delete [] array;
}

template <typename T>
void matrix_print(T** array, int rows, int cols)
{
    for (int i = 0; i < rows; i++)
    {
        for (int j = 0; j < cols; j++)
            cout << array[i][j] << " ";
        cout << endl;
    }
}

void matrix_fill(int** array, int rows, int cols)
{
    for (int i = 0; i < rows; i++)
        for (int j = 0; j < cols; j++)
            array[i][j] = i * cols + j;
}

void matrix_partition(int starting_rows[], int world_size)
{
  starting_rows[0] = 0;
  int rows_left = ROWS;
  for(int i = 1; i < world_size - 1; i++)
  {
    int delta = ceil((double)rows_left/(world_size - i));
    rows_left -= delta;
    starting_rows[i] = starting_rows[i - 1] + delta;
  }
  starting_rows[world_size - 1] = ROWS;
}

template <typename T>
T** matrix_merge(T** fragments, int starting_rows[], int active_workers)
{
  T** matrix_transposed = matrix_create<T>(COLS, ROWS);

  for(int i = 0; i < active_workers; i++)
  {
    int num_rows = starting_rows[i + 1] - starting_rows[i];
    for(int j = 0; j < COLS; j++)
      for(int k = 0; k < num_rows; k++)
        matrix_transposed[j][starting_rows[i] + k] = fragments[i][j * num_rows + k];
  }

  return matrix_transposed;
}

template <typename T>
int rows_dispatching(T** matrix, int starting_rows[], int world_size, int world_rank)
{
  int active_workers = world_size - 1;
  for(int i = 0; i < world_size - 1; i++)
  {
    int num_rows = starting_rows[i + 1] - starting_rows[i];
    cout << "[" << world_rank << "]: Sending rows ["<< starting_rows[i] << "; " << starting_rows[i+1]-1 << "] to " << i << endl;
    MPI_Send(&num_rows, 1, MPI_INT, i, 0, MPI_COMM_WORLD);
    cout << "[" << world_rank << "]: Sent num_rows: " << num_rows << " to " << i << endl;

    if(num_rows > 0)
    {
      MPI_Send((T *)&matrix[starting_rows[i]][0], num_rows*COLS, MPI_INT, i, 1, MPI_COMM_WORLD);
      cout << "[" << world_rank << "]: Sent fragment to " << i << endl;
    }
    else
      active_workers--;
  }

  return active_workers;
}

template <typename T>
T** collecting_results(int starting_rows[], int active_workers, int world_rank)
{
  T** fragments = new T*[active_workers];
  for(int i = 0; i < active_workers; i++)
  {
    int num_rows = starting_rows[i + 1] - starting_rows[i];
    fragments[i] = new T[num_rows*COLS];
    MPI_Recv(fragments[i], num_rows*COLS, MPI_INT, i, 2, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
    cout << "[" << world_rank << "]: Received processed fragment from " << i << endl;
  }
  return fragments;
}

void fragment_processing(int world_size, int world_rank)
{
  int num_rows;
  MPI_Recv(&num_rows, 1, MPI_INT,  world_size - 1, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
  cout << "[" << world_rank << "]: Received num_rows: " << num_rows << " from " << 0 << endl;

  if (num_rows > 0)
  {
    int fragment[num_rows*COLS];
    MPI_Recv(fragment, num_rows*COLS, MPI_INT,  world_size - 1, 1, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
    cout << "[" << world_rank << "]: Received fragment from " << 0 << endl;

    for (int i = 0; i < num_rows*COLS; i++)
      cout << fragment[i] << " ";
    cout << endl;

    int** transposed_fragment = matrix_create<int>(COLS, num_rows);
    int it = 0;
    for (int i = 0; i < num_rows; i++)
      for (int j = 0; j < COLS; j++)
        transposed_fragment[j][i] = fragment[it++];

    cout << "[" << world_rank << "]: Transposed fragment:" << endl;
    matrix_print(transposed_fragment, COLS, num_rows);
    cout << "[" << world_rank << "]: Sending transposed fragment to " << world_size - 1 << endl;
    MPI_Send((int*)&transposed_fragment[0][0], num_rows*COLS, MPI_INT, world_size - 1, 2, MPI_COMM_WORLD);
    cout << "[" << world_rank << "]: Sent transposed fragment to " << world_size - 1 << endl;

    matrix_delete(transposed_fragment);
  }
}

void work_coordination(int world_size, int world_rank)
{
  int** matrix = matrix_create<int>(ROWS, COLS);
  matrix_fill(matrix, ROWS, COLS);
  cout << "[" << world_rank << "]: Initial matrix:" << endl;
  matrix_print(matrix, ROWS, COLS);

  int starting_rows[world_size];
  matrix_partition(starting_rows, world_size);

  int active_workers = rows_dispatching(matrix, starting_rows, world_size, world_rank);

  int** fragments = collecting_results<int>(starting_rows, active_workers, world_rank);

  int** transposed_matrix = matrix_merge(fragments, starting_rows, active_workers);
  cout << "[" << world_rank << "]: Transposed matrix:" << endl;
  matrix_print(transposed_matrix, COLS, ROWS);

  matrix_delete(transposed_matrix);
  for(int i = 0; i < active_workers; i++)
    delete [] fragments[i];
  delete [] fragments;
  matrix_delete(matrix);
}

int main()
{
  MPI_Init(NULL, NULL);

  int world_rank;
  MPI_Comm_rank(MPI_COMM_WORLD, &world_rank);
  int world_size;
  MPI_Comm_size(MPI_COMM_WORLD, &world_size);

  if(world_rank == world_size - 1)
    work_coordination(world_size, world_rank);
  else
    fragment_processing(world_size, world_rank);

  MPI_Finalize();

  return 0;
}

/*
 * base_actor.h
 *
 *  Created on: 2018-3-9
 *      Author: moxiaobo
 */

#ifndef BASE_ACTOR_H_
#define BASE_ACTOR_H_

#include <vector>
#include <time.h>
#include <pthread.h>
#include <unistd.h>

#include <iostream>
#include <ostream>
#include <string>
#include <cstring>
#include <sys/prctl.h>
#include <sys/sysinfo.h>
class BaseActor {
  private:
    static size_t actor_quantity_;
    static std::vector<BaseActor*> actors_;

    void add_actor();

  protected:
    pthread_t thread_id_;
    pthread_attr_t thread_attr_;
    int thread_policy_;
    int thread_priority_;
    size_t stack_size_;
    bool is_start_ = false;
    /// when @see ::StopAllActors(), whether need to join this pthread;
    /// @retval true: main() wait for this thread
    /// @retval false: main() exit, then this thread is exited by OS.
    bool attach_to_main_;

    static pthread_barrier_t barrier_;


    static void * RunEntrance(void*);

    virtual void* RunRoutine(void*);

  public:
    BaseActor(int thread_priority = 10, int thread_policy = SCHED_RR, size_t stack_size = 0, int cpu = -1);
    virtual ~BaseActor();


    static int EnableStart();

    int Start();
    int SetName(std::string name);

    void set_attach_to_main(bool attach_to_main = true);

    static int StartAllActors(void* value);

    static int StopAllActors(void* value);

//  static int ClearAllActors(void* value);
}; // end of BaseActor



#endif /* BASE_ACTOR_H_ */

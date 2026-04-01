`timescale 1ns/1ps

module tb_mux2to1;
    reg a, b, sel;
    wire y;

    mux2to1 dut (
        .a(a),
        .b(b),
        .sel(sel),
        .y(y)
    );

    initial begin
        $dumpfile("wave.vcd");
        $dumpvars(0, tb_mux2to1);
        
        $display("=== Test Start ===");
        
        #0 a=0; b=0; sel=0;
        #1 $display("time=%0t a=%b b=%b sel=%b y=%b", $time, a, b, sel, y);
        
        #10 a=1; b=0; sel=0;
        #1 $display("time=%0t a=%b b=%b sel=%b y=%b", $time, a, b, sel, y);
        
        #10 a=0; b=1; sel=1;
        #1 $display("time=%0t a=%b b=%b sel=%b y=%b", $time, a, b, sel, y);
        
        #10 a=1; b=0; sel=1;
        #1 $display("time=%0t a=%b b=%b sel=%b y=%b", $time, a, b, sel, y);
        
        #10 $display("=== Test End ===");
        $finish;
    end
endmodule
